from pymavlink import mavutil

list_uav = ["udpout:<ip-hp-machine>:14560"]

noti_conn = mavutil.mavlink_connection("udp:0.0.0.0:14551")
# list_uav = ["udpout:127.0.0.1:14560"]

file_policy = "./policy/policy.rego"

while True:
    msg = noti_conn.recv_match(blocking=True)

    msg_type = msg.get_type()
    print(f"Received MAVLink message: {msg_type}")

    if msg:
        # msg_type = msg.get_type()
        if msg_type == "NAMED_VALUE_FLOAT":
            number_data = msg.value
            print(f"Received Named Value Float: {msg.name} = {number_data}")
            break
        # else:
        #     print(f"Received MAVLink message: {msg_type}")
