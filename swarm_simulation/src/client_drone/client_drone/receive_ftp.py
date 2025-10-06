import rclpy
from rclpy.node import Node
from pymavlink import mavutil
from std_msgs.msg import String
import requests

import os

TIMER_PERIOD = 0.1


class MAVLinkFTPReceiver(Node):
    def __init__(self):
        super().__init__("mavlink_ftp_receiver")
        self.publisher_ = self.create_publisher(String, "mavlink_ftp_data", 10)
        self.mav_conn = mavutil.mavlink_connection("udp:0.0.0.0:14561")

        self.mav_send = mavutil.mavlink_connection("udpout:127.0.0.1:14570")

        # Define OPA server URL
        self.opa_server = os.getenv(
            "OPA_URL", "http://localhost:8181/v1/policies/policy.rego"
        )
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
                self.send_file_to_opa(self.received_data)

                self.received_data = b""

    def send_file_to_opa(self, policy_data):
        """Sends policy data to OPA and saves it locally if rejected"""
        try:
            clean_policy = policy_data.replace(b"\x00", b"").strip()

            response = requests.put(self.opa_server, data=clean_policy)

            if response.status_code == 200:
                self.get_logger().info(" File sent to OPA successfully")
                self.send_notification_to_gcs(response.status_code)
            else:
                self.error_opa += 1
                self.get_logger().error(f" OPA rejected file: {response.status_code}")
                self.save_file_locally(policy_data)  # Save for debugging
                self.send_notification_to_gcs(response.status_code)

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

    def send_notification_to_gcs(self, message):
        """
        Send a NAMED_VALUE_FLOAT as a short, robust notification.
        - name: up to 10 bytes ASCII (we pad/truncate)
        - value: float (we put HTTP status code as float when available, else 1.0 for OK)

        Examples:
        message = 200       -> name "OPA200" (bytes), value 200.0
        message = "OK"      -> name "OK" (bytes), value 1.0
        message = "ERR42"   -> name "ERR42", value 0.0
        """
        try:
            self.get_logger().info(f"Sending notification to GCS: {message!r}")

            # compute time_boot_ms
            time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296

            # Normalize message -> short ASCII name and value
            NAME_MAX = 10

            # convert different message types to a short string
            if isinstance(message, (bytes, bytearray)):
                text = message.decode("utf-8", errors="replace")
            elif isinstance(message, (set, list, tuple)):
                # single-element set common mistake: {200}
                if len(message) == 1:
                    text = str(next(iter(message)))
                else:
                    text = ",".join(str(x) for x in message)
            else:
                text = str(message)

            text = text.replace("\x00", "").strip()

            # If the text is a pure integer (e.g. "200"), use OPA prefix for clarity
            if text.isdigit():
                name_field = f"OPA{text}"
                value_float = float(int(text))
            else:
                # heuristics: if text contains "ok"/"success" -> value 1.0, else 0.0
                lowered = text.lower()
                if "ok" in lowered or "done" in lowered or "success" in lowered:
                    value_float = 1.0
                else:
                    # default: 0.0 for non-success textual messages
                    value_float = 0.0
                # keep the name short
                name_field = text

            # encode to ASCII bytes (replace non-ascii), pad/truncate to NAME_MAX
            name_bytes = name_field.encode("ascii", errors="replace")[:NAME_MAX]
            if len(name_bytes) < NAME_MAX:
                name_bytes = name_bytes.ljust(NAME_MAX, b"\x00")

            # Send the named_value_float (name as bytes, value as float)
            try:
                self.mav_send.mav.named_value_float_send(
                    time_boot_ms, name_bytes, float(value_float)
                )
                self.get_logger().info(
                    f"NAMED_VALUE_FLOAT sent: name={name_bytes!r} value={value_float}"
                )
            except Exception as e:
                # attempt the str variant if bytes variant fails on this pymavlink
                try:
                    name_str = name_bytes.rstrip(b"\x00").decode(
                        "ascii", errors="replace"
                    )
                    self.mav_send.mav.named_value_float_send(
                        time_boot_ms, name_str, float(value_float)
                    )
                    self.get_logger().info(
                        f"NAMED_VALUE_FLOAT sent (str fallback): name={name_str!r} value={value_float}"
                    )
                except Exception as e2:
                    self.get_logger().warn(
                        f"named_value_float_send failed both bytes and str forms: {e} / {e2}"
                    )

        except Exception as e:
            self.get_logger().error(f"Error sending notification: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = MAVLinkFTPReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
