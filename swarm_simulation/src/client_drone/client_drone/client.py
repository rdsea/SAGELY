import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import random, time, os, yaml, requests, etcd3, logging
from threading import Timer, Thread, Event
from pydantic import BaseModel
from typing import Optional

# ---------- globals you already use ----------
EDGE_SERVER_NOTIFY_URL = ""
EDGE_SERVER_HEARTBEAT_URL = ""
EDGE_SERVER_UPDATE_COUNTER_URL = ""
EDGE_SERVER_GET_COUNTER_URL = ""
EDGE_SERVER_GET_COMMAND_URL = ""
EDGE_SERVER_GET_LEADER_URL = ""
EDGE_SERVER_SEND_IMG = ""
GROUP_ID = ""
NODE_ID = ""
DS_PATH = ""
RATE = ""
COUNTER_INCREMENT = 1
HEADER = {}
etcd = None
stop_event = Event()  # <-- ensure it exists from the start
_request_timer_started = False  # <-- prevent multiple image timers
# --- request sender control + connection reuse ---
sender_started = False
sender_stop = Event()
session = requests.Session()  # keep-alive across requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------- your helpers (unchanged) ----------
# keep: formalize_HEADER, notify_edge_server, send_heartbeat, update_counter, ...
# BUT: in update_counter() guard the image timer start:


def extract_synset_id(image_path: str) -> str | None:
    """Return the synset id from '<name>_<synset>.(jpg|jpeg)'; None if not present."""
    name = os.path.splitext(os.path.basename(image_path))[0]
    parts = name.rsplit("_", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1]
    return None


# def main_send_request(url, group_id, node_id, req_rate, ds_path):
#     files = os.listdir(ds_path)
#     jpeg_images_list = [f for f in files if f.lower().endswith(".jpeg")]
#     requesting_interval = 1.0 / req_rate
#     timer = Timer(
#         requesting_interval,
#         send_request,
#         args=(url, requesting_interval, jpeg_images_list, ds_path),
#     )
#     timer.daemon = True
#     timer.start()


def update_counter(node_id, group_id, stop_event):
    global sender_started, sender_stop, _request_timer_started
    current_counter = get_counter(group_id)
    current_leader = get_leader(group_id)
    print(f"current leader: {current_leader} vs node id: {node_id}")

    if current_leader == node_id:
        logger.info(f"Header: {HEADER}")
        # start the image sender ONCE
        if not _request_timer_started:
            _request_timer_started = True
            try:
                HEADER["Timestamp"] = str(int(time.time() * 1000))
                start_image_sender(EDGE_SERVER_SEND_IMG, RATE, DS_PATH)
            except Exception as e:
                logger.error(f"Failed to start image sender: {e}")

        while not stop_event.is_set():
            current_counter += COUNTER_INCREMENT
            try:
                response = requests.post(
                    EDGE_SERVER_UPDATE_COUNTER_URL,
                    headers=HEADER,
                    json={
                        "leader_id": node_id,
                        "group_id": group_id,
                        "counter": current_counter,
                    },
                    timeout=(2, 10),
                )
                response.raise_for_status()
                logger.info(
                    f"Counter updated to {current_counter} by leader {node_id} of group {group_id}"
                )
            except requests.RequestException as e:
                logger.error(f"Failed to update counter: {e}")
            stop_event.wait(5)

    # when we exit the loop (leadership over), stop sender and allow it to be restarted later
    sender_stop.set()
    sender_started = False
    _request_timer_started = False


# def update_counter(node_id, group_id, stop_event):
#     global _request_timer_started
#     current_counter = get_counter(group_id)
#     current_leader = get_leader(group_id)
#     print(f"current leader: {current_leader} vs node id: {node_id}")
#
#     if current_leader == node_id:
#         logger.info(f"Header: {HEADER}")
#         # start the image sender ONCE
#         if not _request_timer_started:
#             _request_timer_started = True
#             try:
#                 main_send_request(
#                     EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, RATE, DS_PATH
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to start image sender: {e}")
#
#         while not stop_event.is_set():
#             current_counter += COUNTER_INCREMENT
#             try:
#                 response = requests.post(
#                     EDGE_SERVER_UPDATE_COUNTER_URL,
#                     headers=HEADER,
#                     json={
#                         "leader_id": node_id,
#                         "group_id": group_id,
#                         "counter": current_counter,
#                     },
#                 )
#                 response.raise_for_status()
#                 logger.info(
#                     f"Counter updated to {current_counter} by leader {node_id} of group {group_id}"
#                 )
#             except requests.RequestException as e:
#                 logger.error(f"Failed to update counter: {e}")
#             stop_event.wait(5)


# ---------- the fixed ROS2 node ----------
class ClientNode(Node):
    def __init__(self):
        super().__init__("client_node")

        # declare + read parameters once
        self.declare_parameter("yaml_file", "client_config.yaml")
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

        self.get_logger().info(f"Current working directory: {os.getcwd()}")
        self._load_yaml_and_init()

        # simple sensor publisher
        # self.publisher_ = self.create_publisher(Float32, "sensor_data", 10)
        # self.timer = self.create_timer(1.0, self._timer_callback)

        # start leader monitor in background
        self.leader_thread = Thread(target=monitor_leader, daemon=True)
        self.leader_thread.start()

    def _load_yaml_and_init(self):
        global \
            EDGE_SERVER_NOTIFY_URL, \
            EDGE_SERVER_HEARTBEAT_URL, \
            EDGE_SERVER_UPDATE_COUNTER_URL
        global \
            EDGE_SERVER_GET_COUNTER_URL, \
            EDGE_SERVER_GET_COMMAND_URL, \
            EDGE_SERVER_GET_LEADER_URL
        global EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, DS_PATH, RATE, etcd

        if not os.path.exists(self.yaml_file):
            self.get_logger().error(f"YAML file {self.yaml_file} does not exist")
            return

        with open(self.yaml_file) as f:
            data = yaml.safe_load(f) or {}
        drone_data = data.get(self.drone_id, {})

        server_url = drone_data.get("server_url")
        device_id = drone_data.get("device_id")
        group_id = drone_data.get("group_id")
        ds_path = drone_data.get("ds_path")
        rate = drone_data.get("rate")
        etcd_host = drone_data.get("etcd_host")

        if not (
            server_url and device_id and group_id and ds_path and rate and etcd_host
        ):
            self.get_logger().error("Missing required fields in YAML for this drone_id")
            return

        host, port = etcd_host.split(":")
        # set globals used by your other functions
        GROUP_ID = group_id
        NODE_ID = device_id
        DS_PATH = ds_path
        RATE = rate

        EDGE_SERVER_NOTIFY_URL = server_url + "/notify-leader"
        EDGE_SERVER_HEARTBEAT_URL = server_url + "/heartbeat"
        EDGE_SERVER_UPDATE_COUNTER_URL = server_url + "/update-counter"
        EDGE_SERVER_GET_COUNTER_URL = server_url + "/get-counter"
        EDGE_SERVER_GET_LEADER_URL = server_url + "/get-leader"
        EDGE_SERVER_GET_COMMAND_URL = server_url + "/get-command"
        EDGE_SERVER_SEND_IMG = server_url + "/preprocessing"

        etcd = etcd3.client(host=host, port=int(port))
        formalize_HEADER()

        self.get_logger().info(
            f"Initialized etcd at {host}:{port}, NODE_ID={NODE_ID}, GROUP_ID={GROUP_ID}"
        )

    def _timer_callback(self):
        msg = Float32()
        msg.data = random.uniform(0.0, 100.0)
        self.publisher_.publish(msg)
        self.get_logger().info(f"Publishing: {msg.data}")


# ---------- keep your existing election helpers (campaign_for_leadership, monitor_leader, etc.) ----------
# No behavioral change needed, except they now run because we actually start monitor_leader()
# (You already call formalize_HEADER() where needed.)
# Consider adding daemon=True to threads you spawn inside campaign_for_leadership().


class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None


class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None


def formalize_HEADER():
    global HEADER
    HEADER = {
        # "Host": "object-classification.test.com",
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
        # stop instantly if we lost leadership
        if get_current_leader(group_id) != node_id:
            logger.info("No longer leader; stopping heartbeat loop.")
            break
        try:
            response = requests.post(
                EDGE_SERVER_HEARTBEAT_URL,
                headers=HEADER,
                json={"leader_id": node_id, "group_id": group_id},
                timeout=(2, 10),
            )
            response.raise_for_status()
            logger.info(
                f"Heartbeat sent to edge server by leader {node_id} of group {group_id}"
            )
            etcd.put(f"/election/{group_id}/heartbeat", str(time.time()))
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat: {e}")
        stop_event.wait(5)


# def send_heartbeat(node_id, group_id, stop_event):
#     while not stop_event.is_set():
#         try:
#             response = requests.post(
#                 EDGE_SERVER_HEARTBEAT_URL,
#                 headers=HEADER,
#                 json={"leader_id": node_id, "group_id": group_id},
#             )
#             response.raise_for_status()
#             logger.info(
#                 f"Heartbeat sent to edge server by leader {node_id} of group {group_id}"
#             )
#             etcd.put(f"/election/{group_id}/heartbeat", str(time.time()))
#         except requests.RequestException as e:
#             logger.error(f"Failed to send heartbeat: {e}")
#         stop_event.wait(5)  # Sleep for 5 seconds between heartbeats


# def update_counter(node_id, group_id, stop_event):
#     current_counter = get_counter(group_id)
#     current_leader = get_leader(group_id)
#
#     print(f"current leader: {current_leader} vs node id: {node_id}")
#
#     if current_leader == node_id:
#         logger.info(f"Header: {HEADER}")
#         while not stop_event.is_set():
#             current_counter += COUNTER_INCREMENT
#             try:
#                 # can edit to async
#                 response = requests.post(
#                     EDGE_SERVER_UPDATE_COUNTER_URL,
#                     headers=HEADER,
#                     json={
#                         "leader_id": node_id,
#                         "group_id": group_id,
#                         "counter": current_counter,
#                     },
#                 )
#                 response.raise_for_status()
#                 logger.info(
#                     f"Counter updated to {current_counter} by leader {node_id} of group {group_id}"
#                 )
#
#                 # main_send_request(EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, RATE, DS_PATH)
#                 main_send_request(
#                     EDGE_SERVER_SEND_IMG, GROUP_ID, NODE_ID, RATE, DS_PATH
#                 )
#
#             except requests.RequestException as e:
#                 logger.error(f"Failed to update counter: {e}")
#             stop_event.wait(5)  # Sleep for 5 seconds between counter updates
#


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
    global \
        GROUP_ID, \
        COUNTER_INCREMENT, \
        stop_event, \
        _request_timer_started, \
        sender_started, \
        sender_stop
    while True:
        try:
            with etcd.lock(f"/election/{GROUP_ID}") as _:
                etcd.put(f"/election/{GROUP_ID}/leader", NODE_ID)
                logger.info(f"I am the leader now for group {GROUP_ID}: {NODE_ID}")
                notify_edge_server(NODE_ID, GROUP_ID)

                stop_event = Event()
                heartbeat_thread = Thread(
                    target=send_heartbeat,
                    args=(NODE_ID, GROUP_ID, stop_event),
                    daemon=True,
                )
                command_thread = Thread(
                    target=poll_commands, args=(stop_event,), daemon=True
                )
                counter_thread = Thread(
                    target=update_counter,
                    args=(NODE_ID, GROUP_ID, stop_event),
                    daemon=True,
                )
                heartbeat_thread.start()
                command_thread.start()
                counter_thread.start()

                # monitor leadership; if the etcd leader key changes, end this epoch
                while not stop_event.is_set():
                    val = etcd.get(f"/election/{GROUP_ID}/leader")[0]
                    if val is None:
                        # key missing? treat as lost
                        logger.info("Leader key missing—ending leadership epoch.")
                        break
                    current = val.decode("utf-8")
                    if current != NODE_ID:
                        logger.info(
                            f"Leadership transferred to {current}. Ending epoch."
                        )
                        break
                    time.sleep(1)

                # signal threads to stop and clean sender flags for the next epoch
                stop_event.set()
                sender_stop.set()
                sender_started = False
                _request_timer_started = False

                logger.info(f"Resigned from leadership for group {GROUP_ID}: {NODE_ID}")
        except etcd3.exceptions.Etcd3Exception as e:
            logger.error(f"Failed to campaign for leadership: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        time.sleep(1)


# def campaign_for_leadership():
#     global GROUP_ID, COUNTER_INCREMENT, stop_event
#     while True:
#         try:
#             with etcd.lock(f"/election/{GROUP_ID}") as _:
#                 etcd.put(f"/election/{GROUP_ID}/leader", NODE_ID)
#                 logger.info(f"I am the leader now for group {GROUP_ID}: {NODE_ID}")
#                 notify_edge_server(NODE_ID, GROUP_ID)
#
#                 stop_event = Event()
#                 heartbeat_thread = Thread(
#                     target=send_heartbeat, args=(NODE_ID, GROUP_ID, stop_event)
#                 )
#                 heartbeat_thread.start()
#
#                 command_thread = Thread(target=poll_commands, args=(stop_event,))
#                 command_thread.start()
#
#                 counter_thread = Thread(
#                     target=update_counter, args=(NODE_ID, GROUP_ID, stop_event)
#                 )
#                 counter_thread.start()
#
#                 heartbeat_thread.join()
#                 command_thread.join()
#                 counter_thread.join()
#                 logger.info(f"Resigned from leadership for group {GROUP_ID}: {NODE_ID}")
#         except etcd3.exceptions.Etcd3Exception as e:
#             logger.error(f"Failed to campaign for leadership: {e}")
#         except Exception as e:
#             logger.error(f"Unexpected error: {e}")
#         time.sleep(1)


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


# def change_group(new_group_id):
#     global GROUP_ID, stop_event
#     logger.info(f"Changing group ID from {GROUP_ID} to {new_group_id}")
#     # clear old epoch data
#     etcd.delete(f"/election/{GROUP_ID}/leader")
#     etcd.delete(f"/election/{GROUP_ID}/heartbeat")
#     GROUP_ID = new_group_id
#     etcd.put(f"/nodes/{NODE_ID}/group", GROUP_ID)
#     # end current epoch; the long-running monitor thread will start a new one
#     stop_event.set()
#     # DO NOT call monitor_leader() here


def change_node_id(new_node_id):
    global NODE_ID
    logger.info(f"Changing node ID from {NODE_ID} to {new_node_id}")
    NODE_ID = new_node_id
    etcd.put(f"/nodes/{NODE_ID}/id", NODE_ID)


# def send_request(url, requesting_interval, jpeg_images_list, ds_path):
#     timer = Timer(
#         requesting_interval,
#         send_request,
#         args=(
#             url,
#             requesting_interval,
#             jpeg_images_list,
#             ds_path,
#         ),
#     )
#     timer.start()
#
#     random_image = random.choice(jpeg_images_list)
#     image_path = os.path.join(ds_path, random_image)
#
#     synset_id = extract_synset_id(image_path) or "unknown"
#
#     # TODO: current use extract synset_id function
#     # Extract the synset_id from the file name,
#     #
#     # root, _ = os.path.splitext(image_path)
#     # _, synset_id = os.path.basename(root).rsplit("_", 1)
#
#     # Open the image file as binary
#     with open(image_path, "rb") as img_file:
#         img_data = img_file.read()
#
#     start_time = time.time()
#     file = {"file": ("random_image", img_data, "image/jpeg")}
#
#     try:
#         # # explicit connect/read timeouts
#         # r = session.post(url, headers=HEADER, files=files, timeout=(2, 15))
#         # r.raise_for_status()
#         # # ... log response/json ...
#         #
#         response = requests.post(url, headers=HEADER, files=file)
#         response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
#
#         # Try to parse the response content as JSON
#         try:
#             response_json = response.json()
#         except ValueError:
#             logger.error("Response is not in JSON format")
#             response_json = None
#
#         # Print the JS response, synset_id, and the request time
#         logger.info(
#             f"Response: {response_json}, Synset ID: {synset_id}, Time: {(time.time() - start_time) * 1000}"
#         )
#
#     except requests.RequestException as e:
#         logger.error(f"Request failed: {e}")
#     # response = requests.post(url, headers=HEADER, files=file)
#     # print(response.json(), synset_id, (time.time() - start_time) * 1000)
#     #
#     # response = requests.post(url, headers=HEADER, files=file)


def start_image_sender(url: str, req_rate: float, ds_path: str):
    """Start one background loop that POSTs images at req_rate."""
    global sender_started, sender_stop
    if sender_started:
        return
    files = [
        f
        for f in os.listdir(ds_path)
        if f.lower().endswith((".jpg", ".jpeg"))
        and os.path.isfile(os.path.join(ds_path, f))
    ]
    if not files:
        logger.error(f"No .jpg/.jpeg files found in {ds_path}")
        return
    sender_stop.clear()
    t = Thread(
        target=send_request_loop, args=(url, req_rate, files, ds_path), daemon=True
    )
    t.start()
    sender_started = True


def send_request_loop(url: str, req_rate: float, jpeg_images_list, ds_path: str):
    """Loop: pick an image, POST, sleep; stops when sender_stop is set."""
    interval = 1.0 / float(req_rate)
    while not sender_stop.is_set():
        try:
            random_image = random.choice(jpeg_images_list)
            image_path = os.path.join(ds_path, random_image)
            if not os.path.isfile(image_path):
                continue

            synset_id = extract_synset_id(image_path) or "unknown"
            with open(image_path, "rb") as img_file:
                files = {"file": ("random_image", img_file.read(), "image/jpeg")}

            start_time = time.time()
            # explicit connect/read timeouts
            r = session.post(url, headers=HEADER, files=files, timeout=(2, 15))
            r.raise_for_status()
            try:
                response_json = r.json()
            except ValueError:
                logger.error("Response is not in JSON format")
                response_json = None

            logger.info(
                f"Response: {response_json}, Synset ID: {synset_id}, "
                f"Time: {(time.time() - start_time) * 1000:.2f} ms"
            )
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"send_request_loop error: {e}")
        finally:
            # pace the loop regardless of success/failure
            if not sender_stop.is_set():
                time.sleep(interval)


# def main_send_request(url, group_id, node_id, req_rate, ds_path):
#     # device_id = self.device_id
#     # ds_path = self.ds_path
#     # req_rate = self.rate
#     # url = self.server_url
#
#     files = os.listdir(ds_path)
#     jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
#     requesting_interval = 1.0 / req_rate
#
#     timer = Timer(
#         requesting_interval,
#         send_request,
#         args=(
#             url,
#             requesting_interval,
#             jpeg_images_list,
#             ds_path,
#         ),
#     )
#     timer.start()


def main(args=None):
    rclpy.init(args=args)
    node = ClientNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
