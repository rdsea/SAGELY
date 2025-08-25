import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, String
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2


class DDS2PX4Forwarder(Node):
    def __init__(self):
        super().__init__("dds2px4_forwarder")

        self.get_logger().info("Initializing DDS2PX4Forwarder node")

        # MAVLink connection for sending data to PX4
        self.mav_send = mavutil.mavlink_connection("udpout:127.0.0.1:14550")
        self.get_logger().info(
            "MAVLink connection for sending data established on udpout:127.0.0.1:14550"
        )

        # MAVLink connection for receiving data from PX4 on port 14561
        self.mav_recv = mavutil.mavlink_connection("udp:0.0.0.0:14561")
        self.get_logger().info(
            "MAVLink connection for receiving data established on udp:0.0.0.0:14561"
        )

        # Subscription to ROS2 topic
        self.subscription = self.create_subscription(
            Float64, "number_data", self.listener_callback, 10
        )
        self.get_logger().info("Subscribed to ROS2 topic 'number_data'")

        # Publisher for policy data received from MAVLink
        self.publisher_ = self.create_publisher(String, "policy_data", 10)

        # Timer to check for incoming MAVLink messages
        self.timer = self.create_timer(0.1, self.check_for_mavlink_messages)

    def listener_callback(self, msg):
        number = msg.data
        time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296
        named_value_float = mavlink2.MAVLink_named_value_float_message(
            time_boot_ms=time_boot_ms, name=b"number", value=number
        )
        try:
            self.mav_send.mav.send(named_value_float)
            self.get_logger().info(f"Sent number to PX4: {number}")
        except Exception as e:
            self.get_logger().error(f"Failed to send number: {str(e)}")

    def check_for_mavlink_messages(self):
        # Non-blocking reception of messages
        msg = self.mav_recv.recv_match(blocking=False)
        if msg:
            msg_type = msg.get_type()
            if msg_type == "NAMED_VALUE_FLOAT":
                policy_data = msg.value
                self.get_logger().info(f"Received policy data: {policy_data}")
                # Publish the policy data to a ROS2 topic
                pub_msg = String()
                pub_msg.data = str(policy_data)
                self.publisher_.publish(pub_msg)
            # else:
            #     self.get_logger().info(
            #         f"Received non-NAMED_VALUE_FLOAT message type: {msg_type}"
            #     )
        else:
            self.get_logger().info("No MAVLink message received in this cycle")


def main(args=None):
    rclpy.init(args=args)
    node = DDS2PX4Forwarder()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
