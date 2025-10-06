import time
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2

# Create a connection to listen to MAVLink messages from PX4
conn_recv = mavutil.mavlink_connection("udp:0.0.0.0:14551")
# Create a connection to send MAVLink messages back to PX4
conn_send = mavutil.mavlink_connection("udpout:127.0.0.1:14560")


# Function to send policy data
def send_policy_data(policy_data):
    time_boot_ms = int(time.time() * 1000) % 4294967296  # System time in milliseconds
    named_value_float = mavlink2.MAVLink_named_value_float_message(
        time_boot_ms=time_boot_ms,
        name=b"policy_data",  # 10-character name identifier
        value=policy_data,
    )
    conn_send.mav.send(named_value_float)
    print(f"Sent policy data: {policy_data}")


print("Waiting for MAVLink messages...")

while True:
    # msg = conn_recv.recv_match(blocking=True)
    # if msg:
    #     msg_type = msg.get_type()
    #     if msg_type == "NAMED_VALUE_FLOAT":
    #         number_data = msg.value
    #         print(f"Received Named Value Float: {msg.name} = {number_data}")
    # else:
    #     print(f"Received MAVLink message: {msg_type}")

    # Test sending policy data back
    send_policy_data(123.456)
    time.sleep(5)
