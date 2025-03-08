import rclpy
from rclpy.node import Node
from pymavlink import mavutil
from std_msgs.msg import String
import requests
import json

from pymavlink.dialects.v20 import common as mavlink2

# import time
import os


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

        self.get_logger().info("MAVLink FTP Receiver started on UDP 14561")
        self.timer = self.create_timer(0.1, self.receive_mavftp)

    def receive_mavftp(self):
        msg = self.mav_conn.recv_match(type="FILE_TRANSFER_PROTOCOL", blocking=False)
        if msg:
            payload = msg.payload
            opcode = payload[0]  # Extract opcode
            data_chunk = bytes(payload[12:])  # Ensure data is in bytes

            self.get_logger().info(f"Received FTP message: Opcode {opcode}")

            self.get_logger().info(
                f"📥 Received: Opcode {opcode}, Chunk Size: {len(data_chunk)} bytes"
            )

            if opcode == 10:  # Start of file transfer
                self.logger.info("📂 File Transfer Started")
                self.received_data = b""  # Reset buffer
                self.transfer_active = True

            elif opcode == 4 and self.transfer_active:  # Data chunk
                self.received_data += data_chunk
                self.get_logger().info(
                    f"📦 Data received: {len(self.received_data)} bytes so far"
                )

            elif opcode == 5 and self.transfer_active:  # Transfer complete
                self.get_logger().info(
                    f"✅ File Transfer Completed! Total size: {len(self.received_data)} bytes"
                )
                self.transfer_active = False
                self.send_file_to_opa(self.received_data)
            if opcode == 5:  # End of file transfer
                self.get_logger().info("File Transfer Completed Successfully!")

                self.uploaded_file_path = "/policy/policy.rego"  # Define full file path
                self.received_data = data_chunk  # Store data as bytes

                # self.upload_file_to_opa(self.uploaded_file_path)

                self.write_file(
                    self.uploaded_file_path, self.received_data
                )  # Write file
                file_content = self.read_file(self.uploaded_file_path)  # Verify file

                if file_content:
                    self.send_file_to_opa(self.uploaded_file_path)  # Upload to OPA
                else:
                    self.get_logger().error("File read verification failed")

    # def write_file(self, file_path, data):
    #     """Writes data to a file as bytes."""
    #     try:
    #         os.makedirs(
    #             os.path.dirname(file_path), exist_ok=True
    #         )  # Ensure directory exists
    #         with open(file_path, "wb") as file:  # Open in binary mode
    #             file.write(data)  # Write bytes, not string
    #         self.get_logger().info(f"File written successfully: {file_path}")
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to write file: {str(e)}")
    #         self.send_notification_to_gcs("File write failed")

    def write_file(self, file_path, data):
        """Writes the received data to a file, removing extra null bytes."""
        try:
            os.makedirs(
                os.path.dirname(file_path), exist_ok=True
            )  # Ensure directory exists

            cleaned_data = data.rstrip(b"\x00")  # Remove trailing null bytes

            with open(file_path, "wb") as file:
                file.write(cleaned_data)  # Write cleaned bytes
            self.get_logger().info(f"File written successfully: {file_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to write file: {str(e)}")
            self.send_notification_to_gcs("File write failed")

    def read_file(self, file_path):
        """Reads the file to verify content."""
        try:
            with open(file_path, "rb") as file:
                content = file.read()  # Read as bytes
            self.get_logger().info(
                f"File read successfully: {file_path}, Size: {len(content)} bytes"
            )
            return content
        except Exception as e:
            self.get_logger().error(f"Failed to read file: {str(e)}")
            return None

    # def receive_mavftp(self):
    #     """Receives MAVLink FTP messages and processes file transfers before uploading to OPA."""
    #     msg = self.mav_conn.recv_match(type="FILE_TRANSFER_PROTOCOL", blocking=False)
    #     if msg:
    #         payload = msg.payload
    #         opcode = payload[0]  # Extract opcode
    #         data = (
    #             bytes(payload[12:]).decode(errors="ignore").strip()
    #         )  # Decode filename
    #
    #         self.get_logger().info(
    #             f"Received FTP message: Opcode {opcode}, Data: {data}"
    #         )
    #
    #         if opcode == 10:  # Start of file transfer
    #             self.uploaded_file_path = f"/policy/{data}"  # Ensure correct file path
    #             self.received_data = b""  # Reset buffer
    #             self.get_logger().info(
    #                 f"File Transfer Started: {self.uploaded_file_path}"
    #             )
    #
    #         elif opcode == 4:  # Receiving data chunk
    #             self.received_data += bytes(payload[12:])
    #             self.get_logger().info(f"Receiving Chunk: {len(payload[12:])} bytes")
    #
    #         # elif opcode == 11:  # File transfer complete
    #         elif opcode == 5:  # File transfer complete
    #             self.get_logger().info(f"File Transfer Completed Successfully!")
    #
    #             # Ensure directory exists before writing
    #             # os.makedirs(os.path.dirname(self.uploaded_file_path), exist_ok=True)
    #
    #             # Write the received data to the correct file path
    #             try:
    #                 with open(self.uploaded_file_path, "wb") as file:
    #                     file.write(self.received_data)
    #                 self.get_logger().info(
    #                     f"File successfully written to {self.uploaded_file_path}"
    #                 )
    #
    #                 # Now upload the file to OPA
    #                 self.upload_file_to_opa(data)
    #
    #             except Exception as e:
    #                 self.get_logger().error(f"Failed to write file: {str(e)}")
    #                 self.send_notification_to_gcs("File Write Failed")
    #
    # def receive_mavftp(self):
    #     msg = self.mav_conn.recv_match(type="FILE_TRANSFER_PROTOCOL", blocking=False)
    #     if msg:
    #         payload = msg.payload
    #         opcode = payload[0]  # Extract opcode
    #
    #         data = (
    #             bytes(payload[12:]).decode(errors="ignore").strip()
    #         )  # Decode filename
    #
    #         self.get_logger().info(
    #             f"Received FTP message: Opcode {opcode}, Data: {data}"
    #         )

    # try:
    #     # Read the file
    #     # with open(file_path, "rb") as file:
    #     #     file_data = file.read()
    #
    #     # Send file to OPA
    #     # data must to be a binary instead of string
    #     response = requests.put(self.opa_server, data=data)
    #
    #     if response.status_code == 200:
    #         self.get_logger().info("File sent to OPA successfully")
    #
    #         verify_response = requests.get(self.opa_server)
    #
    #         if verify_response.status_code == 200:
    #             policy_data = (
    #                 json.loads(verify_response.content)
    #                 .get("result", {})
    #                 .get("raw", "")
    #             )
    #             self.get_logger().info("Policy Uploaded Successfully...")
    #             self.send_notification_to_gcs("OPA Upload OK:")
    #         else:
    #             self.get_logger().error(
    #                 f"Verification failed: {verify_response.status_code}"
    #             )
    #             self.send_notification_to_gcs("OPA Upload Failed")
    #
    #     else:
    #         self.get_logger().error(
    #             f"Failed to upload file to OPA: {response.status_code}"
    #         )
    #         self.send_notification_to_gcs("OPA Upload Failed")
    #
    # except Exception as e:
    #     self.get_logger().error(f"Error sending file to OPA: {str(e)}")
    #     self.send_notification_to_gcs("OPA Upload Error")
    #
    # if opcode == 10:  # Start of file transfer
    #     self.uploaded_file_path = (
    #         f"/root/{data}" if data else "/root/policy.rego"
    #     )
    #     self.received_data = b""  # Reset the received data buffer
    #     self.get_logger().info(
    #         f"File Transfer Started: {self.uploaded_file_path}"
    #     )
    #     self.get_logger().info(f"print: {self.received_data}")
    #
    #     self.create_or_open_file(self.uploaded_file_path)
    #     #
    #     # self.get_logger().info(f" Chunk: {len(data)} bytes")
    #
    # elif opcode == 4:
    #     self.get_logger().info(f"Receiving Chunk: {len(data)} bytes")

    #         if opcode == 5:
    #             self.get_logger().info(
    #                 f"Received FTP message 555: Opcode {opcode}, Data: {data}"
    #             )
    #             self.uploaded_file_path = "/policy/policy.rego"  # Define full file path
    #             self.write_file(self.uploaded_file_path, data)  # Write file to disk
    #             file_content = self.read_file(
    #                 self.uploaded_file_path
    #             )  # Read file to verify
    #
    #             if file_content:
    #                 self.send_file_to_opa(self.uploaded_file_path)  # Upload to OPA
    #             else:
    #                 self.get_logger().error("File read verification failed")
    #
    # def write_file(self, file_path, data):
    #     """Writes data to the file."""
    #     try:
    #         os.makedirs(
    #             os.path.dirname(file_path), exist_ok=True
    #         )  # Ensure directory exists
    #         with open(file_path, "wb") as file:
    #             file.write(data)
    #         self.get_logger().info(f"File written successfully: {file_path}")
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to write file: {str(e)}")
    #         self.send_notification_to_gcs("File write failed")
    #
    # def read_file(self, file_path):
    #     """Reads the file to verify content."""
    #     try:
    #         with open(file_path, "rb") as file:
    #             content = file.read()
    #         self.get_logger().info(
    #             f"File read successfully: {file_path}, Size: {len(content)} bytes"
    #         )
    #         return content
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to read file: {str(e)}")
    #         return None

    #             self.get_logger().info("File Transfer Completed Successfully!")
    #             self.received_data = data
    #             self.create_or_open_file(self.uploaded_file_path)
    #
    #             self.write_file(self.uploaded_file_path)
    #             self.send_file_to_opa(self.uploaded_file_path)
    #             self.received_data = b""
    #
    # def create_or_open_file(self, file_path):
    #     """Creates or opens the file for writing."""
    #     try:
    #         self.file = open(file_path, "wb")  # Open the file in write-binary mode
    #         self.get_logger().info(f"File created/opened: {file_path}")
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to create/open file: {str(e)}")
    #         self.send_notification_to_gcs("Failed to open file for writing")
    #
    # def write_file(self, file_path):
    #     """Writes the received data to the file."""
    #     try:
    #         self.get_logger(f"File written successfully: {self.received_data}")
    #         if self.file:
    #             self.file.write(self.received_data)  # Write all the received data
    #             self.file.close()  # Close the file after writing
    #             self.get_logger().info(f"File written successfully: {file_path}")
    #         else:
    #             self.get_logger().error("File handle is None, failed to write.")
    #     except Exception as e:
    #         self.get_logger().error(f"Failed to write file: {str(e)}")
    #         self.send_notification_to_gcs("File write failed")

    def send_file_to_opa(self, file_path):
        """Reads the uploaded file from PX4 and sends it to an OPA server."""

        try:
            # Read the file
            with open(file_path, "rb") as file:
                file_data = file.read()

            # Send file to OPA

            # self.get_logger().info(f"File ready to send to OPA {file_data}")

            response = requests.put(self.opa_server, data=file_data)

            self.get_logger().info(f"result from {response}")
            if response.status_code == 200:
                self.get_logger().info("File sent to OPA successfully")

                verify_response = requests.get(self.opa_server)

                if verify_response.status_code == 200:
                    policy_data = (
                        json.loads(verify_response.content)
                        .get("result", {})
                        .get("raw", "")
                    )
                    self.get_logger().info("Policy Uploaded Successfully...")
                    self.send_notification_to_gcs("OPA Upload OK:")
                else:
                    self.get_logger().error(
                        f"Verification failed: {verify_response.status_code}"
                    )
                    self.send_notification_to_gcs("OPA Upload Failed")

            else:
                self.get_logger().error(
                    f"Failed to upload file to OPA: {response.status_code}"
                )
                self.send_notification_to_gcs("OPA Upload Failed")

        except Exception as e:
            self.get_logger().error(f"Error sending file to OPA: {str(e)}")
            self.send_notification_to_gcs("OPA Upload Error")

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
