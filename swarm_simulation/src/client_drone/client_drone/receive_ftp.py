import rclpy
from rclpy.node import Node
from pymavlink import mavutil
from std_msgs.msg import String
import requests

from pymavlink.dialects.v20 import common as mavlink2

# import time
import os

TIMER_PERIOD = 0.1


class MAVLinkFTPReceiver(Node):
    def __init__(self):
        super().__init__("mavlink_ftp_receiver")
        self.publisher_ = self.create_publisher(String, "mavlink_ftp_data", 10)
        self.mav_conn = mavutil.mavlink_connection("udp:0.0.0.0:14561")

        self.mav_send = mavutil.mavlink_connection("udpout:127.0.0.1:14550")

        # Define OPA server URL
        self.opa_server = "http://localhost:8181/v1/policies/policy.rego"

        # Default path where PX4 stores received files
        self.uploaded_file_path = "/policy/policy.rego"
        self.received_data = b""
        # self.transfer_active = False  # Track if a file transfer is in progress

        self.get_logger().info("MAVLink FTP Receiver started on UDP 14561")
        self.timer = self.create_timer(TIMER_PERIOD, self.receive_mavftp)
        self.error_transit = 0
        self.error_opa = 0

    def receive_mavftp(self):
        """Handles incoming MAVLink FTP messages"""

        self.get_logger().info(f"Error transit {self.error_transit}")
        self.get_logger().info(f"Error OPA {self.error_opa}")
        msg = self.mav_conn.recv_match(type="FILE_TRANSFER_PROTOCOL", blocking=False)
        if msg:
            payload = msg.payload
            opcode = payload[0]  # Extract opcode
            data = bytes(payload[12:]).strip()  # Extract data

            self.get_logger().info(f"Received FTP message: Opcode {opcode}")
            if opcode == 11:  # Start of file transfer
                self.get_logger().info("Start File Transfer")
                if self.received_data != b"":
                    self.error_transit += 1
                self.received_data = b""

            if opcode == 5:
                self.get_logger().info(
                    f" Data received: {len(self.received_data)} bytes so far"
                )
                self.received_data += data

            elif opcode == 6:  # File transfer complete
                self.get_logger().info("File Transfer Completed Successfully!")
                # data_to_opa = (
                #     self.received_data.encode()
                # )  # Convert to bytes before sending
                self.send_file_to_opa(self.received_data)

                self.received_data = b""

                self.send_notification_to_gcs("DONE")
                # number = 1.32
                # time_boot_ms = (
                #     self.get_clock().now().nanoseconds // 1000000
                # ) % 4294967296
                # named_value_float = mavlink2.MAVLink_named_value_float_message(
                #     time_boot_ms=time_boot_ms, name=b"number", value=number
                # )
                # try:
                #     self.mav_send.mav.send(named_value_float)
                #     self.get_logger().info(f"Sent number to PX4: {number}")
                # except Exception as e:
                #     self.get_logger().error(f"Failed to send number: {str(e)}")

    def send_file_to_opa(self, policy_data):
        """Sends policy data to OPA and saves it locally if rejected"""
        try:
            clean_policy = policy_data.replace(b"\x00", b"").strip()

            response = requests.put(self.opa_server, data=clean_policy)

            if response.status_code == 200:
                self.get_logger().info(" File sent to OPA successfully")
            else:
                self.error_opa += 1
                self.get_logger().error(f" OPA rejected file: {response.status_code}")
                self.save_file_locally(policy_data)  # Save for debugging

        except Exception as e:
            self.get_logger().error(f" Error sending file to OPA: {str(e)}")
            self.save_file_locally(policy_data)  # Save on unexpected errors

    def save_file_locally(self, data):
        """Saves policy data to a local file if OPA upload fails"""
        try:
            os.makedirs(os.path.dirname(self.uploaded_file_path), exist_ok=True)
            with open(self.uploaded_file_path, "wb") as file:
                file.write(data)
            self.get_logger().info(f" File saved locally at {self.uploaded_file_path}")
        except Exception as e:
            self.get_logger().error(f" Failed to save file: {str(e)}")

    #
    def send_notification_to_gcs(self, message):
        """Sends a MAVLink STATUSTEXT message to notify the GCS."""
        self.get_logger().info(f"Sending notification to GCS: {message}")
        # self.mav_send.mav.statustext_send(
        #     mavutil.mavlink.MAV_SEVERITY_INFO,  # Severity level
        #     message.encode(),  # Convert message to bytes
        # )
        time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296
        named_value_float = mavlink2.MAVLink_named_value_float_message(
            time_boot_ms=time_boot_ms, name=b"number", value=1
        )
        self.mav_send.mav.send(named_value_float)


def main(args=None):
    rclpy.init(args=args)
    node = MAVLinkFTPReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
