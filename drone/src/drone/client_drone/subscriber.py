# import rclpy
# from rclpy.node import Node
# from px4_msgs.msg import VehicleCommand
#
#

# import rclpy
# from rclpy.node import Node
# from pymavlink import mavutil
# from pymavlink.dialects.v20 import common as mavlink2

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
# class DDS2PX4Forwarder(Node):
#     def __init__(self):
#         super().__init__("dds2px4_forwarder")
#
#         # MAVLink connection setup to PX4 (MAVLink instance on port 14550)
#         self.mav = mavutil.mavlink_connection("udpout:127.0.0.1:14550")
#         self.subscription = self.create_subscription(
#             Float64, "number_data", self.listener_callback, 10
#         )
#
#     def listener_callback(self, msg):
#         number = msg.data
#
#         # Ensure time_boot_ms fits within valid range
#         time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296
#
#         named_value_float = mavlink2.MAVLink_named_value_float_message(
#             time_boot_ms=time_boot_ms,
#             name=b"number",  # 10-character name identifier
#             value=number,
#         )
#         try:
#             self.mav.mav.send(named_value_float)
#             self.get_logger().info(f"Sent number to PX4: {number}")
#         except Exception as e:
#             self.get_logger().error(f"Failed to send number: {str(e)}")
#
#     def check_for_mavlink_messages(self):
#         # Non-blocking reception of messages
#         msg = self.mav.recv_match(blocking=False)
#         if msg:
#             msg_type = msg.get_type()
#             if msg_type == "NAMED_VALUE_FLOAT":
#                 policy_data = msg.value
#                 self.get_logger().info(f"Received policy data: {policy_data}")
#                 # Publish the policy data to a ROS2 topic
#                 pub_msg = String()
#                 pub_msg.data = str(policy_data)
#                 self.publisher_.publish(pub_msg)
#
#
# def main(args=None):
#     rclpy.init(args=args)
#     node = DDS2PX4Forwarder()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()
#
#
# if __name__ == "__main__":
#     main()

# class SimplePX4Commander(Node):
#     def __init__(self):
#         super().__init__("simple_px4_commander")
#
#         # MAVLink connection setup (simulated GCS port)
#         self.mav = mavutil.mavlink_connection("udpout:127.0.0.1:14551")
#
#         # Timers to send various messages periodically
#         self.heartbeat_timer = self.create_timer(1.0, self.send_heartbeat)
#         self.custom_data_timer = self.create_timer(4.0, self.send_scaled_pressure2)
#
#     def send_heartbeat(self):
#         heartbeat = mavlink2.MAVLink_heartbeat_message(
#             type=mavlink2.MAV_TYPE_QUADROTOR,
#             autopilot=mavlink2.MAV_AUTOPILOT_PX4,
#             base_mode=mavlink2.MAV_MODE_MANUAL_ARMED,
#             custom_mode=0,
#             system_status=mavlink2.MAV_STATE_ACTIVE,
#             mavlink_version=3,
#         )
#         self.mav.mav.send(heartbeat)
#         self.get_logger().info("Sent HEARTBEAT message")
#
#     def send_scaled_pressure2(self):
#         time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296
#         scaled_pressure2 = mavlink2.MAVLink_scaled_pressure2_message(
#             time_boot_ms=time_boot_ms,
#             press_abs=1013.25,
#             press_diff=0.0,
#             temperature=2000,
#         )
#         try:
#             self.mav.mav.send(scaled_pressure2)
#             self.get_logger().info(
#                 f"Sent SCALED_PRESSURE2 message: time_boot_ms={time_boot_ms}, press_abs={scaled_pressure2.press_abs}, temperature={scaled_pressure2.temperature}"
#             )
#         except Exception as e:
#             self.get_logger().error(
#                 f"Failed to send SCALED_PRESSURE2 message: {str(e)}"
#             )
#
#
# def main(args=None):
#     rclpy.init(args=args)
#     node = SimplePX4Commander()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()
#
#
# if __name__ == "__main__":
#     main()

# class PX4Commander(Node):
#     def __init__(self):
#         super().__init__("px4_commander")
#         self.publisher = self.create_publisher(
#             VehicleCommand, "/fmu/in/vehicle_command", 10
#         )
#         self.arm_timer = self.create_timer(
#             1.0, self.send_command
#         )  # Send arm command every second
#
#         # MAVLink connection setup (simulated GCS port)
#         self.mav = mavutil.mavlink_connection(
#             "udp:127.0.0.1:14551"
#         )  # Adjust port as needed
#         self.custom_data_timer = self.create_timer(
#             2.0, self.send_custom_data
#         )  # Send custom data every 2 seconds
#
#     def send_command(self):
#         msg = VehicleCommand()
#         msg.timestamp = (
#             self.get_clock().now().nanoseconds // 1000
#         )  # Convert to microseconds
#         msg.command = 22  # Command ID for ARM/DISARM
#         msg.param1 = 1.0  # 1.0 = Arm, 0.0 = Disarm
#         msg.target_system = 1
#         msg.target_component = 1
#         msg.source_system = 1
#         msg.source_component = 1
#         msg.from_external = True
#         self.publisher.publish(msg)
#         self.get_logger().info("Sent ARM command to PX4")
#         # Sending the same command via MAVLink for testing
#         arm_command = mavlink2.MAVLink_command_long_message(
#             target_system=1,
#             target_component=1,
#             command=22,
#             confirmation=0,
#             param1=1.0,
#             param2=0,
#             param3=0,
#             param4=0,
#             param5=0,
#             param6=0,
#             param7=0,
#         )
#         self.mav.mav.send(arm_command)
#
#     def send_custom_data(self):
#         # Calculate time since boot in milliseconds, ensure it's within 0 <= number <= 4294967295
#         time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296
#         scaled_pressure2 = mavlink2.MAVLink_scaled_pressure2_message(
#             time_boot_ms=time_boot_ms,  # time since boot in ms
#             press_abs=1013.25,  # Replace with your actual pressure data
#             press_diff=0.0,  # Differential pressure; replace with actual data
#             temperature=2000,  # Temperature in centidegrees Celsius; replace as needed
#         )
#         self.mav.mav.send(scaled_pressure2)
#         self.get_logger().info("Sent SCALED_PRESSURE2 data to GCS")
#
#
# def main(args=None):
#     rclpy.init(args=args)
#     node = PX4Commander()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()
#
#
# if __name__ == "__main__":
#     main()
# class PX4Commander(Node):
#     def __init__(self):
#         super().__init__('px4_commander')
#         self.publisher = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', 10)
#         self.timer = self.create_timer(1.0, self.send_command)  # Send every second
#
#     def send_command(self):
#         msg = VehicleCommand()
#         msg.timestamp = self.get_clock().now().nanoseconds // 1000  # Convert to microseconds
#         msg.command = 22  # Command ID for ARM/DISARM
#         msg.param1 = 1.0  # 1.0 = Arm, 0.0 = Disarm
#         msg.target_system = 1
#         msg.target_component = 1
#         msg.source_system = 1
#         msg.source_component = 1
#         msg.from_external = True
#         self.publisher.publish(msg)
#         self.get_logger().info("Sent ARM command to PX4")
#
# def main(args=None):
#     rclpy.init(args=args)
#     node = PX4Commander()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()
#
# if __name__ == '__main__':
#     main()
#
#

##!/usr/bin/env python3
#
# import rclpy
# from rclpy.node import Node
# from std_msgs.msg import Float32
# import random
#
#
# class SensorPublisher(Node):
#    def __init__(self):
#        super().__init__("sensor_publisher")
#        self.publisher_ = self.create_publisher(Float32, "sensor_data", 10)
#        timer_period = 1.0  # seconds
#        self.timer = self.create_timer(timer_period, self.timer_callback)
#
#    def timer_callback(self):
#        msg = Float32()
#        msg.data = random.uniform(0.0, 100.0)
#        self.publisher_.publish(msg)
#        self.get_logger().info(f"Publishing: {msg.data}")
#
#
# def main(args=None):
#    rclpy.init(args=args)
#    sensor_publisher = SensorPublisher()
#    rclpy.spin(sensor_publisher)
#    sensor_publisher.destroy_node()
#    rclpy.shutdown()
#
#
# if __name__ == "__main__":
#    main()
