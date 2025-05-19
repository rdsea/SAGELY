from pymavlink import mavutil

# Create a connection to listen to MAVLink messages
conn = mavutil.mavlink_connection("udp:127.0.0.1:14551")

print("Waiting for MAVLink messages...")

while True:
    msg = conn.recv_match(blocking=True)
    if msg:
        msg_type = msg.get_type()
        if msg_type == "NAMED_VALUE_FLOAT":
            number_data = msg.value
            print(f"Received Named Value Float: {msg.name} = {number_data}")
        else:
            print(f"Received MAVLink message: {msg_type}")

# from pymavlink import mavutil
#
# # Create a connection to listen to MAVLink messages
# conn = mavutil.mavlink_connection("udp:127.0.0.1:14551")
#
# print("Waiting for MAVLink messages...")
#
# while True:
#     msg = conn.recv_match(blocking=True)
#     if msg:
#         msg_type = msg.get_type()
#         if msg_type == "SCALED_PRESSURE2":
#             sensor_value = msg.press_abs
#             temperature = msg.temperature
#             print(
#                 f"Received SCALED_PRESSURE2: press_abs={sensor_value}, temperature={temperature}"
#             )
#         else:
#             print(f"Received MAVLink message: {msg_type}")
# from pymavlink import mavutil
#
#
# # Connect to MAVLink (Adjust the connection type and port as needed)
# mav = mavutil.mavlink_connection("udp:127.0.0.1:14550")
#
# print("Waiting for MAVLink messages...")
#
# while True:
#     msg = mav.recv_match(blocking=True)
#     if msg:
#         try:
#             msg_type = msg.get_type()
#         except KeyError:
#             msg_type = "UNKNOWN"
#
#         if msg_type == "SCALED_PRESSURE2":
#             sensor_value = (
#                 msg.press_abs
#             )  # This will be the data from ROS2 forwarded by PX4
#             print(f"Received Sensor Data: {sensor_value}")
#         elif msg_type.startswith("UNKNOWN"):
#             print(f"Received {msg_type}: {msg}")
#             print(f"Raw data: {msg.get_msgbuf()}")
#         else:
#             print(f"Received MAVLink message: {msg}")
