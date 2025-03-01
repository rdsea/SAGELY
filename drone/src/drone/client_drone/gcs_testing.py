from pymavlink import mavutil

# Connect to MAVLink (Adjust the connection type and port as needed)
mav = mavutil.mavlink_connection("udp:127.0.0.1:14551")

print("Waiting for MAVLink messages...")

while True:
    try:
        msg = mav.recv_match(blocking=True)
        if msg:
            print(f"Received MAVLink message: {msg}")

            if msg.get_type() == "SCALED_PRESSURE2":
                press_abs = msg.press_abs  # These will be the pressure data
                temperature = (
                    msg.temperature
                )  # These will be the temperature data (in centidegrees Celsius)
                print(
                    f"Received SCALED_PRESSURE2 data: Pressure = {press_abs} mbar, Temperature = {temperature / 100.0} °C"
                )

            if msg.get_type() == "COMMAND_LONG":
                target_system = msg.target_system
                target_component = msg.target_component
                command = msg.command
                param1 = msg.param1
                print(
                    f"Received COMMAND_LONG data: Command = {command}, Param1 = {param1}, Target System = {target_system}, Target Component = {target_component}"
                )

    except Exception as e:
        print(f"Error receiving MAVLink message: {e}")
