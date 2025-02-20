import socket
import mavutil


def mavlink_listener(server_ip, server_port):
    # Create a MAVLink connection
    mav_conn = mavutil.mavlink_connection(f"udp:{server_ip}:{server_port}")

    while True:
        msg = mav_conn.recv_match()
        if msg:
            print(f"Received message: {msg}")


if __name__ == "__main__":
    server_ip = "0.0.0.0"  # Listen on all interfaces
    server_port = 14550  # The port to listen on

    mavlink_listener(server_ip, server_port)
