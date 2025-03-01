from pymavlink import mavutil

# Connect to MAVLink (Adjust the connection type and port as needed)
mav = mavutil.mavlink_connection("udp:0.0.0.0:14550")

print("Waiting for MAVLink messages...")

while True:
    msg = mav.recv_match(blocking=True)
    if msg:
        # print(f"Received MAVLink message: {msg}")

        # Check if it's the SCALED_PRESSURE2 message
        if msg.get_type() == "SCALED_PRESSURE2":
            sensor_value = (
                msg.press_abs
            )  # This will be the data from ROS2 forwarded by PX4
            print(f"Received Sensor Data: {sensor_value}")
