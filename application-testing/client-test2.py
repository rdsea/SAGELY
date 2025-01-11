import etcd3
import time
import requests
from threading import Thread, Event
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace these with your actual URLs
EDGE_SERVER_NOTIFY_URL = "http://localhost:8080/notify-leader"
EDGE_SERVER_HEARTBEAT_URL = "http://localhost:8080/heartbeat"
EDGE_SERVER_UPDATE_COUNTER_URL = "http://localhost:8080/update-counter"
EDGE_SERVER_GET_COUNTER_URL = "http://localhost:8080/get-counter"
EDGE_SERVER_GET_COMMAND_URL = "http://localhost:8080/get-command"

# Initialize etcd client
def initialize_etcd_client():
    etcd_client = etcd3.client()
    return etcd_client

etcd = initialize_etcd_client()

NODE_ID = "node-1"
GROUP_ID = "group-1"
COUNTER_INCREMENT = 1  # Initial counter increment value

class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None

class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None

def notify_edge_server(node_id, group_id):
    try:
        response = requests.post(EDGE_SERVER_NOTIFY_URL, json={"leader_id": node_id, "group_id": group_id})
        response.raise_for_status()
        logger.info(f"Edge server notified about new leader for group {group_id}: {node_id}")
    except requests.RequestException as e:
        logger.error(f"Failed to notify edge server: {e}")

def send_heartbeat(node_id, group_id, stop_event):
    while not stop_event.is_set():
        try:
            response = requests.post(EDGE_SERVER_HEARTBEAT_URL, json={"leader_id": node_id, "group_id": group_id})
            response.raise_for_status()
            logger.info(f"Heartbeat sent to edge server by leader {node_id} of group {group_id}")
            etcd.put(f"/election/{group_id}/heartbeat", str(time.time()))
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat: {e}")
        stop_event.wait(5)  # Sleep for 5 seconds between heartbeats

def update_counter(node_id, group_id, stop_event):
    current_counter = get_counter(group_id)
    while not stop_event.is_set():
        current_counter += COUNTER_INCREMENT
        try:
            response = requests.post(EDGE_SERVER_UPDATE_COUNTER_URL, json={"leader_id": node_id, "group_id": group_id, "counter": current_counter})
            response.raise_for_status()
            logger.info(f"Counter updated to {current_counter} by leader {node_id} of group {group_id}")
        except requests.RequestException as e:
            logger.error(f"Failed to update counter: {e}")
        stop_event.wait(5)  # Sleep for 5 seconds between counter updates

def get_counter(group_id):
    try:
        response = requests.get(EDGE_SERVER_GET_COUNTER_URL, params={"group_id": group_id})
        response.raise_for_status()
        return response.json().get("counter", 0)
    except requests.RequestException as e:
        logger.error(f"Failed to get counter: {e}")
        return 0

def delete_command(node_id, command_type):
    try:
        response = requests.delete(f"{EDGE_SERVER_GET_COMMAND_URL}/{node_id}/{command_type}")
        response.raise_for_status()
        logger.info(f"Command {command_type} for node {node_id} deleted from server")
    except requests.RequestException as e:
        logger.error(f"Failed to delete command: {e}")

def get_current_leader(group_id):
    try:
        leader_key = f"/election/{group_id}/leader"
        leader = etcd.get(leader_key)
        return leader[0].decode('utf-8') if leader[0] is not None else None
    except Exception as e:
        logger.error(f"Failed to get current leader: {e}")
        return None

def follow_leader(leader, group_id, stop_event):
    while not stop_event.is_set():
        try:
            logger.info(f"Following leader {leader} of group {group_id}")
            response = requests.post(EDGE_SERVER_HEARTBEAT_URL, json={"leader_id": leader, "group_id": group_id})
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat as follower: {e}")
            break
        time.sleep(5)

def poll_commands(stop_event):
    global GROUP_ID, NODE_ID, COUNTER_INCREMENT
    while not stop_event.is_set():
        try:
            for command_type in ["change-group-or-id", "change-task-parameter"]:
                response = requests.get(f"{EDGE_SERVER_GET_COMMAND_URL}/{NODE_ID}/{command_type}")
                if response.status_code == 200:
                    command_value = response.json().get("command")
                    if command_type == "change-group-or-id":
                        command = ChangeGroupOrIDCommand.model_validate_json(command_value)
                        if command.new_group_id and GROUP_ID != command.new_group_id:
                            change_group(command.new_group_id)
                        if command.new_node_id and NODE_ID != command.new_node_id:
                            change_node_id(command.new_node_id)
                        delete_command(NODE_ID, command_type)
                    elif command_type == "change-task-parameter":
                        command = ChangeTaskParameterCommand.model_validate_json(command_value)
                        if command.counter_increment is not None:
                            logger.info(f"Command received, changing counter increment to {command.counter_increment}")
                            COUNTER_INCREMENT = command.counter_increment
                        delete_command(NODE_ID, command_type)
        except Exception as e:
            logger.error(f"Failed to get command: {e}")
        time.sleep(3)

def campaign_for_leadership():
    global GROUP_ID, COUNTER_INCREMENT, stop_event
    while True:
        try:
            with etcd.lock(f"/election/{GROUP_ID}") as lock:
                etcd.put(f"/election/{GROUP_ID}/leader", NODE_ID)
                logger.info(f"I am the leader now for group {GROUP_ID}: {NODE_ID}")
                notify_edge_server(NODE_ID, GROUP_ID)

                stop_event = Event()
                heartbeat_thread = Thread(target=send_heartbeat, args=(NODE_ID, GROUP_ID, stop_event))
                heartbeat_thread.start()

                command_thread = Thread(target=poll_commands, args=(stop_event,))
                command_thread.start()

                counter_thread = Thread(target=update_counter, args=(NODE_ID, GROUP_ID, stop_event))
                counter_thread.start()

                heartbeat_thread.join()
                command_thread.join()
                counter_thread.join()
                logger.info(f"Resigned from leadership for group {GROUP_ID}: {NODE_ID}")
        except etcd3.exceptions.Etcd3Exception as e:
            logger.error(f"Failed to campaign for leadership: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        time.sleep(1)

def clean_stale_leader_data(group_id):
    try:
        heartbeat_key = f"/election/{group_id}/heartbeat"
        last_heartbeat = etcd.get(heartbeat_key)[0]
        if last_heartbeat is None or time.time() - float(last_heartbeat.decode('utf-8')) > 10:
            logger.info(f"Stale leader data detected for group {group_id}. Cleaning up.")
            etcd.delete(f"/election/{group_id}/leader")
            etcd.delete(heartbeat_key)
    except Exception as e:
        logger.error(f"Failed to clean stale leader data: {e}")

def monitor_leader():
    global GROUP_ID, NODE_ID, stop_event
    while True:
        clean_stale_leader_data(GROUP_ID)
        current_leader = get_current_leader(GROUP_ID)
        logger.info(f"Current leader: {current_leader}")
        if current_leader is None or current_leader == NODE_ID:
            logger.info(f"Current leader is {current_leader}. Campaigning for leadership.")
            campaign_for_leadership()
        else:
            try:
                heartbeat_key = f"/election/{GROUP_ID}/heartbeat"
                last_heartbeat = etcd.get(heartbeat_key)[0]
                if last_heartbeat is None or time.time() - float(last_heartbeat.decode('utf-8')) > 10:
                    logger.info(f"Leader {current_leader} missed heartbeat. Campaigning for leadership.")
                    etcd.delete(f"/election/{GROUP_ID}/leader")
                    campaign_for_leadership()
            except Exception as e:
                logger.error(f"Failed to check leader heartbeat: {e}")
        time.sleep(5)

def change_group(new_group_id):
    global GROUP_ID, stop_event
    logger.info(f"Changing group ID from {GROUP_ID} to {new_group_id}")
    etcd.delete(f"/election/{GROUP_ID}/leader")

    heartbeat_key = f"/election/{GROUP_ID}/heartbeat"
    etcd.delete(heartbeat_key)
    GROUP_ID = new_group_id
    etcd.put(f"/nodes/{NODE_ID}/group", GROUP_ID)
    stop_event.set()  # Stop the current threads
    stop_event = Event()  # Create a new stop_event for the new threads
    monitor_leader()  # Restart the process with the new group

def change_node_id(new_node_id):
    global NODE_ID
    logger.info(f"Changing node ID from {NODE_ID} to {new_node_id}")
    NODE_ID = new_node_id
    etcd.put(f"/nodes/{NODE_ID}/id", NODE_ID)

if __name__ == "__main__":
    stop_event = Event()
    monitor_leader()
