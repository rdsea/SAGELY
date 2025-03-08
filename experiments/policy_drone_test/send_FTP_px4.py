from pymavlink import mavutil
import time
import struct

# list_uav = ["udpout:130.233.195.221:14560"]

list_uav = ["udpout:127.0.0.1:14560"]

file_policy = "./policy/policy-2.rego"
# MAVLink connection (PX4 MAVLink FTP target)
# conn = mavutil.mavlink_connection("udpout:127.0.0.1:14560")
# noti_conn = mavutil.mavlink_connection("udp:0.0.0.0:14551")


def send_ftp_command(conn, opcode, size=0, session=0, offset=0, data=b""):
    """Send an FTP command via MAVLink"""
    payload = struct.pack("<BBHII", opcode, 0, session, size, offset) + data
    conn.mav.file_transfer_protocol_send(
        target_network=0,
        target_system=1,  # PX4 system ID
        target_component=1,  # PX4 Autopilot component
        payload=payload.ljust(251, b"\0"),  # Pad payload to 251 bytes
    )


def read_file(local_path, remote_path):
    """Upload a file to PX4 via MAVLink FTP"""
    with open(local_path, "rb") as file:
        file_data = file.read()

    file_size = len(file_data)
    print(f"Uploading {local_path} ({file_size} bytes) to {remote_path}")
    return file_size, file_data
    # print(file_data)

    # Open file session
    # send_ftp_command(10, size=len(remote_path) + 1, data=remote_path.encode() + b"\0")
    # time.sleep(0.1)  # Wait for response

    # Send file in chunks


def upload_file(conn, file_size, file_data):
    send_ftp_command(conn, 10)
    chunk_size = 239  # MAVLink FTP max data size
    for offset in range(0, file_size, chunk_size):
        chunk = file_data[offset : offset + chunk_size]
        send_ftp_command(conn, 4, size=len(chunk), offset=offset, data=chunk)
        time.sleep(0.01)  # Avoid overloading PX4

    send_ftp_command(conn, 5)
    print("Upload complete!")


# Example: Upload "test.txt" to PX4 (microSD root)
for uav in list_uav:
    noti_conn = mavutil.mavlink_connection("udp:0.0.0.0:14551")
    file_size, file_data = read_file(file_policy, "policy")

    conn = mavutil.mavlink_connection(uav)

    upload_file(conn, file_size, file_data)

    while True:
        msg = noti_conn.recv_match(blocking=True)

        msg_type = msg.get_type()
        # print(f"Received MAVLink message: {msg_type}")

        if msg:
            # msg_type = msg.get_type()
            if msg_type == "NAMED_VALUE_FLOAT":
                number_data = msg.value
                print(f"Received Named Value Float: {msg.name} = {number_data}")
                break
            # else:
            #     print(f"Received MAVLink message: {msg_type}")
