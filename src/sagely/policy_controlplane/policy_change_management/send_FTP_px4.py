import argparse
import csv
import os
import struct
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Iterable, Optional

from pymavlink import mavutil
from tqdm import tqdm

try:
    import yaml  # optional, only used if --uav-config is provided
except Exception:
    yaml = None

# Defaults (used only if not provided via CLI/env/YAML)
DEFAULT_LIST_UAV: List[Tuple[str, str, str]] = [
    ("hp", "udpout:192.168.49.3:14560", "udp:0.0.0.0:14551"),
]
DEFAULT_FILE_POLICY = "./policy_get_header.rego"

# Experiment Parameters (still configurable via CLI if needed)
TIME_RUNS = 1
ADDED_LATENCY = "0ms_0ms_variable"
ADDED_PACKET_LOSS = "0%"
AVERAGE = 10  # note: currently interpreted as seconds threshold in your code

# Lock for thread-safe CSV writing
csv_lock = threading.Lock()


@dataclass
class UAV:
    name: str
    uav_url: str
    local_url: str


def parse_env_uavs(env_value: str) -> List[UAV]:
    """
    Parse LIST_UAV from env like:
      LIST_UAV="name,uav_url,local_url;name2,uav2,local2"
    """
    uavs: List[UAV] = []
    for item in env_value.split(";"):
        item = item.strip()
        if not item:
            continue
        parts = [p.strip() for p in item.split(",", 2)]
        if len(parts) != 3:
            raise ValueError(
                f"Invalid LIST_UAV item '{item}'. Expected 'name,uav_url,local_url'."
            )
        uavs.append(UAV(parts[0], parts[1], parts[2]))
    return uavs


def load_uavs_from_yaml(path: str) -> List[UAV]:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is not installed; cannot read YAML. `pip install PyYAML`"
        )
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    uavs = []
    for entry in data.get("uavs", []):
        uavs.append(UAV(entry["name"], entry["uav"], entry["local_port"]))
    if not uavs:
        raise ValueError(f"No 'uavs' entries found in {path}")
    return uavs


def resolve_uavs(args) -> List[UAV]:
    # 1) YAML config has highest priority if provided
    if args.uav_config:
        return load_uavs_from_yaml(args.uav_config)

    # 2) One or more --uav flags
    if args.uav:
        return [
            UAV(name, uav_url, local_url) for (name, uav_url, local_url) in args.uav
        ]

    # 3) Environment variable LIST_UAV
    env = os.getenv("LIST_UAV")
    if env:
        return parse_env_uavs(env)

    # 4) Fallback to defaults
    return [UAV(*triple) for triple in DEFAULT_LIST_UAV]


def resolve_file_policy(args) -> str:
    # CLI flag wins
    if args.file_policy:
        return args.file_policy

    # Then env var
    env = os.getenv("FILE_POLICY")
    if env:
        return env

    # Fallback default
    return DEFAULT_FILE_POLICY


def send_ftp_command(conn, opcode, size=0, session=0, offset=0, data=b""):
    """Send an FTP command via MAVLink"""
    # payload: <BBHII  = opcode, 0, session, size, offset  (little-endian)
    payload = struct.pack("<BBHII", opcode, 0, session, size, offset) + data
    conn.mav.file_transfer_protocol_send(
        target_network=0,
        target_system=1,  # PX4 system ID
        target_component=1,  # PX4 Autopilot component
        payload=payload.ljust(251, b"\0"),  # Pad payload to 251 bytes
    )


def read_file(local_path: str) -> Tuple[int, bytes]:
    """Read the file and return its contents"""
    with open(local_path, "rb") as f:
        file_data = f.read()
    return len(file_data), file_data


def upload_file(conn, file_size: int, file_data: bytes):
    """Upload the file to the UAV via MAVLink FTP"""
    send_ftp_command(conn, 10)  # Open file session
    chunk_size = 239  # MAVLink FTP max data size
    for offset in range(0, file_size, chunk_size):
        chunk = file_data[offset : offset + chunk_size]
        send_ftp_command(conn, 4, size=len(chunk), offset=offset, data=chunk)
        time.sleep(0.01)  # Avoid overloading PX4
    send_ftp_command(conn, 5)  # Close file session
    print("Upload complete!")


def send_file_to_uav(uav: UAV, file_policy: str, results_file: Path):
    """Thread function to send a file to a UAV and log latency"""
    noti_conn = mavutil.mavlink_connection(uav.local_url)
    conn = mavutil.mavlink_connection(uav.uav_url)

    file_size, file_data = read_file(file_policy)
    start_time = time.time()

    upload_file(conn, file_size, file_data)

    while True:
        msg = noti_conn.recv_match(blocking=True, timeout=5)
        if msg:
            if msg.get_type() == "NAMED_VALUE_FLOAT":
                latency = time.time() - start_time
                print(
                    f"[{uav.uav_url}] Received Named Value Float: {msg.name} = {msg.value}"
                )
                print(f"[{uav.uav_url}] Time taken: {latency:.4f} sec")

                with csv_lock:
                    with results_file.open(mode="a", newline="") as f:
                        writer = csv.writer(f)
                        if time.time() - start_time < AVERAGE:
                            writer.writerow([uav.name, "inf"])
                        else:
                            writer.writerow([uav.name, latency])
                break

        if time.time() - start_time > 30:  # Timeout case
            with csv_lock:
                with results_file.open(mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([uav.name, "inf"])
            print(f"[{uav.uav_url}] Timeout occurred!")
            break


def build_results_path(file_policy: str) -> Path:
    results_dir = Path("./results")
    results_dir.mkdir(parents=True, exist_ok=True)
    policy_stem = Path(file_policy).stem  # e.g. 'policy_get_header'
    filename = (
        f"latency_{TIME_RUNS}_{ADDED_LATENCY}_{ADDED_PACKET_LOSS}_{policy_stem}.csv"
    )
    return results_dir / filename


def main():
    parser = argparse.ArgumentParser(
        description="Send a policy file to UAV(s) over MAVLink FTP."
    )
    parser.add_argument(
        "--file-policy",
        "-f",
        help="Path to the policy file to upload (overrides FILE_POLICY env).",
    )
    parser.add_argument(
        "--uav",
        nargs=3,
        action="append",
        metavar=("NAME", "UAV_URL", "LOCAL_URL"),
        help="Add a UAV triple. Repeat for multiple UAVs. "
        "Example: --uav hp udpout:192.168.49.3:14560 udp:0.0.0.0:14551",
    )
    parser.add_argument(
        "--uav-config",
        help="YAML file with: uavs: [{name: n, uav: 'udpout:...', local_port: 'udp:...'}, ...]",
    )
    parser.add_argument(
        "--runs", type=int, default=TIME_RUNS, help="Number of transfer iterations."
    )
    args = parser.parse_args()

    file_policy = resolve_file_policy(args)
    if not Path(file_policy).is_file():
        raise FileNotFoundError(f"Policy file not found: {file_policy}")

    uavs = resolve_uavs(args)
    if not uavs:
        raise ValueError("No UAVs specified.")

    results_file = build_results_path(file_policy)

    for _ in tqdm(range(args.runs), desc="File Transfers"):
        threads: List[threading.Thread] = []
        for uav in uavs:
            th = threading.Thread(
                target=send_file_to_uav, args=(uav, file_policy, results_file)
            )
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
        time.sleep(1)


if __name__ == "__main__":
    main()

# python send_policy.py --file-policy ./policy/policy_get_header.rego --uav-config uavs.yaml

# python send_policy.py \
#   --file-policy ./policy/policy_get_header.rego \
#   --uav hp udpout:192.168.49.3:14560 udp:0.0.0.0:14551 \
#   --uav sim udpout:127.0.0.1:14560 udp:0.0.0.0:14553 \
#   --runs 3

# import threading
# import time
# import struct
# import csv
# from pymavlink import mavutil
# from tqdm import tqdm
#
# # List of UAVs and their respective local ports
# LIST_UAV = [
#     ("hp", "udpout:192.168.49.3:14560", "udp:0.0.0.0:14551"),
# ]
#
# # Experiment Parameters
# TIME = 1
# ADDED_LATENCY = "0ms_0ms_variable"
# ADDED_PACKET_LOSS = "0%"
# AVERAGE = 10
# FILE_POLICY = "./policy_get_header.rego"
# RESULTS_FILE = (
#     f"./results/latency_{TIME}_{ADDED_LATENCY}_{ADDED_PACKET_LOSS}_{FILE_POLICY}.csv"
# )
#
# # Lock for thread-safe CSV writing
# csv_lock = threading.Lock()
#
#
# def send_ftp_command(conn, opcode, size=0, session=0, offset=0, data=b""):
#     """Send an FTP command via MAVLink"""
#     payload = struct.pack("<BBHII", opcode, 0, session, size, offset) + data
#     conn.mav.file_transfer_protocol_send(
#         target_network=0,
#         target_system=1,  # PX4 system ID
#         target_component=1,  # PX4 Autopilot component
#         payload=payload.ljust(251, b"\0"),  # Pad payload to 251 bytes
#     )
#
#
# def read_file(local_path):
#     """Read the file and return its contents"""
#     with open(local_path, "rb") as file:
#         file_data = file.read()
#     return len(file_data), file_data
#
#
# def upload_file(conn, file_size, file_data):
#     """Upload the file to the UAV via MAVLink FTP"""
#     send_ftp_command(conn, 10)  # Open file session
#     chunk_size = 239  # MAVLink FTP max data size
#     for offset in range(0, file_size, chunk_size):
#         chunk = file_data[offset : offset + chunk_size]
#         send_ftp_command(conn, 4, size=len(chunk), offset=offset, data=chunk)
#         time.sleep(0.01)  # Avoid overloading PX4
#     send_ftp_command(conn, 5)  # Close file session
#     print("Upload complete!")
#
#
# def send_file_to_uav(uav_name, uav, local_port):
#     """Thread function to send a file to a UAV and log latency"""
#     noti_conn = mavutil.mavlink_connection(local_port)
#     conn = mavutil.mavlink_connection(uav)
#
#     file_size, file_data = read_file(FILE_POLICY)
#     start_time = time.time()
#
#     upload_file(conn, file_size, file_data)
#
#     while True:
#         msg = noti_conn.recv_match(blocking=True, timeout=5)
#         if msg:
#             if msg.get_type() == "NAMED_VALUE_FLOAT":
#                 latency = time.time() - start_time
#                 print(f"[{uav}] Received Named Value Float: {msg.name} = {msg.value}")
#                 print(f"[{uav}] Time taken: {latency:.4f} sec")
#
#                 with csv_lock:
#                     with open(RESULTS_FILE, mode="a", newline="") as file:
#                         writer = csv.writer(file)
#                         if time.time() - start_time < AVERAGE:
#                             writer.writerow([uav_name, "inf"])
#                         else:
#                             writer.writerow([uav_name, latency])
#
#                 break
#
#         if time.time() - start_time > 30:  # Timeout case
#             with csv_lock:
#                 with open(RESULTS_FILE, mode="a", newline="") as file:
#                     writer = csv.writer(file)
#                     writer.writerow([uav_name, "inf"])
#             print(f"[{uav}] Timeout occurred!")
#             break
#
#
# # Main execution loop
# if __name__ == "__main__":
#     for _ in tqdm(range(TIME), desc="File Transfers"):
#         threads = []
#
#         for uav_name, uav, local_port in LIST_UAV:
#             thread = threading.Thread(
#                 target=send_file_to_uav, args=(uav_name, uav, local_port)
#             )
#             thread.start()
#             threads.append(thread)
#
#         for thread in threads:
#             thread.join()  # Wait for all threads to finish before next iteration
#
#         time.sleep(1)  # Small delay before the next round
