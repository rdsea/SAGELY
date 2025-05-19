import threading
import time
import struct
import csv
from pymavlink import mavutil
from tqdm import tqdm

# List of UAVs and their respective local ports
LIST_UAV = [
    ("hp", "udpout:130.233.195.221:14560", "udp:0.0.0.0:14554"),
    # ("bee1", "udpout:130.233.195.214:14560", "udp:0.0.0.0:14551"),
    # ("bee2", "udpout:130.233.195.211:14560", "udp:0.0.0.0:14552"),
    # ("bee3", "udpout:130.233.195.212:14560", "udp:0.0.0.0:14553"),
]

# Experiment Parameters
TIME = 100
ADDED_LATENCY = "0ms_0ms_variable"
ADDED_PACKET_LOSS = "0%"
AVERAGE = 10
FILE_POLICY = "./policy/policy-2.rego"
RESULTS_FILE = (
    f"./results/latency_{TIME}_{ADDED_LATENCY}_{ADDED_PACKET_LOSS}_{FILE_POLICY}.csv"
)

# Lock for thread-safe CSV writing
csv_lock = threading.Lock()


def send_ftp_command(conn, opcode, size=0, session=0, offset=0, data=b""):
    """Send an FTP command via MAVLink"""
    payload = struct.pack("<BBHII", opcode, 0, session, size, offset) + data
    conn.mav.file_transfer_protocol_send(
        target_network=0,
        target_system=1,  # PX4 system ID
        target_component=1,  # PX4 Autopilot component
        payload=payload.ljust(251, b"\0"),  # Pad payload to 251 bytes
    )


def read_file(local_path):
    """Read the file and return its contents"""
    with open(local_path, "rb") as file:
        file_data = file.read()
    return len(file_data), file_data


def upload_file(conn, file_size, file_data):
    """Upload the file to the UAV via MAVLink FTP"""
    send_ftp_command(conn, 10)  # Open file session
    chunk_size = 239  # MAVLink FTP max data size
    for offset in range(0, file_size, chunk_size):
        chunk = file_data[offset : offset + chunk_size]
        send_ftp_command(conn, 4, size=len(chunk), offset=offset, data=chunk)
        time.sleep(0.01)  # Avoid overloading PX4
    send_ftp_command(conn, 5)  # Close file session
    print("Upload complete!")


def send_file_to_uav(uav_name, uav, local_port):
    """Thread function to send a file to a UAV and log latency"""
    noti_conn = mavutil.mavlink_connection(local_port)
    conn = mavutil.mavlink_connection(uav)

    file_size, file_data = read_file(FILE_POLICY)
    start_time = time.time()

    upload_file(conn, file_size, file_data)

    while True:
        msg = noti_conn.recv_match(blocking=True, timeout=5)
        if msg:
            if msg.get_type() == "NAMED_VALUE_FLOAT":
                latency = time.time() - start_time
                print(f"[{uav}] Received Named Value Float: {msg.name} = {msg.value}")
                print(f"[{uav}] Time taken: {latency:.4f} sec")

                with csv_lock:
                    with open(RESULTS_FILE, mode="a", newline="") as file:
                        writer = csv.writer(file)
                        if time.time() - start_time < AVERAGE:
                            writer.writerow([uav_name, "inf"])
                        else:
                            writer.writerow([uav_name, latency])

                break

        if time.time() - start_time > 30:  # Timeout case
            with csv_lock:
                with open(RESULTS_FILE, mode="a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([uav_name, "inf"])
            print(f"[{uav}] Timeout occurred!")
            break


# Main execution loop
if __name__ == "__main__":
    for _ in tqdm(range(TIME), desc="File Transfers"):
        threads = []

        for uav_name, uav, local_port in LIST_UAV:
            thread = threading.Thread(
                target=send_file_to_uav, args=(uav_name, uav, local_port)
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()  # Wait for all threads to finish before next iteration

        time.sleep(1)  # Small delay before the next round
