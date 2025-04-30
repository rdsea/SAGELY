#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import random

import time
import etcd3

from pydantic import BaseModel
from typing import Optional
import logging

EDGE_SERVER_NOTIFY_URL = ""
EDGE_SERVER_HEARTBEAT_URL = ""
EDGE_SERVER_UPDATE_COUNTER_URL = ""
EDGE_SERVER_GET_COUNTER_URL = ""
EDGE_SERVER_GET_COMMAND_URL = ""
EDGE_SERVER_GET_LEADER_URL = ""
GROUP_ID = ""
NODE_ID = ""
EDGE_SERVER_SEND_IMG = ""
DS_PATH = ""
RATE = ""
COUNTER_INCREMENT = 1  # Initial counter increment value
HEADER = {}
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorPublisher(Node):
    def __init__(self):
        super().__init__("sensor_publisher")
        self.publisher_ = self.create_publisher(Float32, "sensor_data", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        msg = Float32()
        msg.data = random.uniform(0.0, 100.0)
        self.publisher_.publish(msg)
        self.get_logger().info(f"Publishing: {msg.data}")
        super().__init__("client_node")
        self.declare_parameter("yaml_file", "client_config.yaml")  # Default YAML file
        self.declare_parameter("drone_id", "")
        self.declare_parameter("group_id", "")
        self.declare_parameter("etcd_host", "")

        self.yaml_file = (
            self.get_parameter("yaml_file").get_parameter_value().string_value
        )
        self.drone_id = (
            self.get_parameter("drone_id").get_parameter_value().string_value
        )
        self.group_id = (
            self.get_parameter("group_id").get_parameter_value().string_value
        )
        self.etcd_host = (
            self.get_parameter("etcd_host").get_parameter_value().string_value
        )
        self.image_paths = []
        # print('yaml file ', self.yaml_file)
        self.load_yaml_data()

    def initialize_etcd_client(self, host, port):
        etcd_client = etcd3.client(
            host=host,  # Replace with your etcd host if different
            port=port,  # Replace with your etcd client port if different
        )
        return etcd_client

    def load_yaml_data(self):
        global \
            EDGE_SERVER_NOTIFY_URL, \
            EDGE_SERVER_HEARTBEAT_URL, \
            EDGE_SERVER_UPDATE_COUNTER_URL, \
            EDGE_SERVER_GET_COUNTER_URL, \
            EDGE_SERVER_GET_COMMAND_URL, \
            EDGE_SERVER_GET_LEADER_URL, \
            etcd, \
            GROUP_ID, \
            NODE_ID, \
            EDGE_SERVER_SEND_IMG, \
            DS_PATH, \
            RATE
        self.get_logger().info(f"Current working directory: {os.getcwd()}")

        if os.path.exists(self.yaml_file):
            with open(self.yaml_file) as file:
                data = yaml.safe_load(file)
                drone_data = data.get(self.drone_id, {})

                self.server_url = drone_data.get("server_url")
                self.device_id = drone_data.get("device_id")
                self.group_id = drone_data.get("group_id")
                self.ds_path = drone_data.get("ds_path")
                self.image_paths = drone_data.get("image_paths")
                self.rate = drone_data.get("rate")
                # self.gps_data = drone_data.get("gps_data")
                self.etcd_host = drone_data.get("etcd_host")
                host, port = self.etcd_host.split(":")

                # Replace these with actual URLs
                EDGE_SERVER_NOTIFY_URL = self.server_url + "/notify-leader"
                EDGE_SERVER_HEARTBEAT_URL = self.server_url + "/heartbeat"
                EDGE_SERVER_UPDATE_COUNTER_URL = self.server_url + "/update-counter"
                EDGE_SERVER_GET_COUNTER_URL = self.server_url + "/get-counter"
                EDGE_SERVER_GET_LEADER_URL = self.server_url + "/get-leader"
                EDGE_SERVER_GET_COMMAND_URL = self.server_url + "/get-command"
                EDGE_SERVER_SEND_IMG = self.server_url + "/preprocessing/"

                NODE_ID = self.device_id
                GROUP_ID = self.group_id
                DS_PATH = self.ds_path
                RATE = self.rate
                # NODE_ID = "node-1"
                # GROUP_ID = "group-1"
                etcd = self.initialize_etcd_client(host=host, port=port)
                formalize_HEADER()

        else:
            self.get_logger().error(f"YAML file {self.yaml_file} does not exist")

    def main(self):
        # stop_event = Event()
        monitor_leader()


class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None


class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None


def formalize_HEADER():
    global HEADER
    HEADER = {
        "Host": "object-classification.test.com",
        "Authorization": f"Basic {NODE_ID}:{GROUP_ID}",
    }


def notify_edge_server(node_id, group_id):
    try:
        response = requests.post(
            EDGE_SERVER_NOTIFY_URL,
            headers=HEADER,
            json={"leader_id": node_id, "group_id": group_id},
        )
        response.raise_for_status()

        # edit the header when become a leader and ready to keep heartbeat
        formalize_HEADER()

        logger.info(
            f"Edge server notified about new leader for group {group_id}: {node_id}"
        )
    except requests.RequestException as e:
        logger.error(f"Failed to notify edge server: {e}")


def send_heartbeat(node_id, group_id, stop_event):
    while not stop_event.is_set():
        try:
            response = requests.post(
                EDGE_SERVER_HEARTBEAT_URL,
                headers=HEADER,
                json={"leader_id": node_id, "group_id": group_id},
            )
            response.raise_for_status()
            logger.info(
                f"Heartbeat sent to edge server by leader {node_id} of group {group_id}"
            )
            etcd.put(f"/election/{group_id}/heartbeat", str(time.time()))
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat: {e}")
        stop_event.wait(5)  # Sleep for 5 seconds between heartbeats


def update_counter(node_id, group_id, stop_event):
    current_counter = get_counter(group_id)
    current_leader = get_leader(group_id)

    print(f"current leader: {current_leader} vs node id: {node_id}")

    if current_leader == node_id:
        logger.info(f"Header: {HEADER}")
        while not stop_event.is_set():
            current_counter += COUNTER_INCREMENT
            try:
                # can edit to async
                response = requests.post(
                    EDGE_SERVER_UPDATE_COUNTER_URL,
                    headers=HEADER,
                    json={
                        "leader_id": node_id,
                        "group_id": group_id,
                        "counter": current_counter,
                    },
                )
                response.raise_for_status()
                logger.info(
                    f"Counter updated to {current_counter} by leader {node_id} of group {group_id}"
                )

                # main_send_request(EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, RATE, DS_PATH)
                main_send_request(
                    EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, RATE, DS_PATH
                )

            except requests.RequestException as e:
                logger.error(f"Failed to update counter: {e}")
            stop_event.wait(5)  # Sleep for 5 seconds between counter updates


def get_counter(group_id):
    try:
        response = requests.get(
            EDGE_SERVER_GET_COUNTER_URL, headers=HEADER, params={"group_id": group_id}
        )
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Received counter response: {json_response}")

        if isinstance(json_response, dict) and "counter" in json_response:
            counter_value = json_response["counter"]
            if isinstance(counter_value, list) and len(counter_value) == 1:
                return counter_value[0]
            return counter_value
        # return response.json().get("counter", 0)
    except requests.RequestException as e:
        logger.error(f"Failed to get counter: {e}")
        return 0


def get_leader(group_id):
    try:
        response = requests.get(
            EDGE_SERVER_GET_LEADER_URL, headers=HEADER, params={"group_id": group_id}
        )
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Received leader response: {json_response}")

        if isinstance(json_response, dict) and "leader_id" in json_response:
            counter_value = json_response["leader_id"]
            if isinstance(counter_value, list) and len(counter_value) == 1:
                return counter_value[0]
            return counter_value
        # return response.json().get("counter", 0)
    except requests.RequestException as e:
        logger.error(f"Failed to get leader_id: {e}")
        return 0


def delete_command(node_id, command_type):
    try:
        # maybe need to check the authorization here again?
        response = requests.delete(
            f"{EDGE_SERVER_GET_COMMAND_URL}/{node_id}/{command_type}",
            headers=HEADER,
        )
        response.raise_for_status()
        logger.info(f"Command {command_type} for node {node_id} deleted from server")
    except requests.RequestException as e:
        logger.error(f"Failed to delete command: {e}")


def get_current_leader(group_id):
    try:
        leader_key = f"/election/{group_id}/leader"
        leader = etcd.get(leader_key)
        return leader[0].decode("utf-8") if leader[0] is not None else None
    except Exception as e:
        logger.error(f"Failed to get current leader: {e}")
        return None


def follow_leader(leader, group_id, stop_event):
    while not stop_event.is_set():
        try:
            logger.info(f"Following leader {leader} of group {group_id}")
            response = requests.post(
                EDGE_SERVER_HEARTBEAT_URL,
                headers=HEADER,
                json={"leader_id": leader, "group_id": group_id},
            )
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
                response = requests.get(
                    f"{EDGE_SERVER_GET_COMMAND_URL}/{NODE_ID}/{command_type}",
                    headers=HEADER,
                )
                if response.status_code == 200:
                    command_list = response.json().get("command")

                    if (
                        command_list
                        and isinstance(command_list, list)
                        and len(command_list) > 0
                    ):
                        command_value = command_list[
                            0
                        ]  # Extract the first command from the list

                        if command_type == "change-group-or-id":
                            command = ChangeGroupOrIDCommand.model_validate_json(
                                command_value
                            )
                            if (
                                command.new_group_id
                                and GROUP_ID != command.new_group_id
                            ):
                                change_group(command.new_group_id)
                            if command.new_node_id and NODE_ID != command.new_node_id:
                                change_node_id(command.new_node_id)
                            delete_command(NODE_ID, command_type)
                        elif command_type == "change-task-parameter":
                            command = ChangeTaskParameterCommand.model_validate_json(
                                command_value
                            )
                            if command.counter_increment is not None:
                                logger.info(
                                    f"Command received, changing counter increment to {command.counter_increment}"
                                )
                                COUNTER_INCREMENT = command.counter_increment
                            delete_command(NODE_ID, command_type)
                    formalize_HEADER()
        except Exception as e:
            logger.error(f"Failed to get command: {e}")
        time.sleep(3)


def campaign_for_leadership():
    global GROUP_ID, COUNTER_INCREMENT, stop_event
    while True:
        try:
            with etcd.lock(f"/election/{GROUP_ID}") as _:
                etcd.put(f"/election/{GROUP_ID}/leader", NODE_ID)
                logger.info(f"I am the leader now for group {GROUP_ID}: {NODE_ID}")
                notify_edge_server(NODE_ID, GROUP_ID)

                stop_event = Event()
                heartbeat_thread = Thread(
                    target=send_heartbeat, args=(NODE_ID, GROUP_ID, stop_event)
                )
                heartbeat_thread.start()

                command_thread = Thread(target=poll_commands, args=(stop_event,))
                command_thread.start()

                counter_thread = Thread(
                    target=update_counter, args=(NODE_ID, GROUP_ID, stop_event)
                )
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
        if (
            last_heartbeat is None
            or time.time() - float(last_heartbeat.decode("utf-8")) > 10
        ):
            logger.info(
                f"Stale leader data detected for group {group_id}. Cleaning up."
            )
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
            logger.info(
                f"Current leader is {current_leader}. Campaigning for leadership."
            )
            campaign_for_leadership()
        else:
            try:
                heartbeat_key = f"/election/{GROUP_ID}/heartbeat"
                last_heartbeat = etcd.get(heartbeat_key)[0]
                if (
                    last_heartbeat is None
                    or time.time() - float(last_heartbeat.decode("utf-8")) > 10
                ):
                    logger.info(
                        f"Leader {current_leader} missed heartbeat. Campaigning for leadership."
                    )
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


def send_request(url, requesting_interval, jpeg_images_list, ds_path):
    timer = Timer(
        requesting_interval,
        send_request,
        args=(
            url,
            requesting_interval,
            jpeg_images_list,
            ds_path,
        ),
    )
    timer.start()

    random_image = random.choice(jpeg_images_list)
    image_path = os.path.join(ds_path, random_image)

    # Extract the synset_id from the file name
    root, _ = os.path.splitext(image_path)
    _, synset_id = os.path.basename(root).rsplit("_", 1)

    # Open the image file as binary
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()

    start_time = time.time()
    file = {"file": ("random_image", img_data, "image/jpeg")}

    try:
        response = requests.post(url, headers=HEADER, files=file)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

        # Try to parse the response content as JSON
        try:
            response_json = response.json()
        except ValueError:
            logger.error("Response is not in JSON format")
            response_json = None

        # Print the JSON response, synset_id, and the request time
        logger.info(
            f"Response: {response_json}, Synset ID: {synset_id}, Time: {(time.time() - start_time) * 1000}"
        )

    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    # response = requests.post(url, headers=HEADER, files=file)
    # print(response.json(), synset_id, (time.time() - start_time) * 1000)
    #
    # response = requests.post(url, headers=HEADER, files=file)


def main_send_request(url, group_id, node_id, req_rate, ds_path):
    # device_id = self.device_id
    # ds_path = self.ds_path
    # req_rate = self.rate
    # url = self.server_url

    files = os.listdir(ds_path)
    jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
    requesting_interval = 1.0 / req_rate

    timer = Timer(
        requesting_interval,
        send_request,
        args=(
            url,
            requesting_interval,
            jpeg_images_list,
            ds_path,
        ),
    )
    timer.start()


def main(args=None):
    rclpy.init(args=args)
    sensor_publisher = SensorPublisher()
    rclpy.spin(sensor_publisher)
    sensor_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
