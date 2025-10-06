from pymavlink import mavutil

# Create a connection to listen to MAVLink messages
conn = mavutil.mavlink_connection("udp:0.0.0.0:14551")

print("Waiting for MAVLink messages...")

while True:
    msg = conn.recv_match(blocking=True)
    if msg:
        msg_type = msg.get_type()
        if msg_type == "NAMED_VALUE_FLOAT":
            number_data = msg.value
            print(f"Received Named Value Float: {msg.name} = {number_data}")
        # else:
        #     print(f"Received MAVLink message: {msg_type}")
