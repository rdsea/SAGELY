import rclpy
from rclpy.node import Node
from px4_msgs.msg import VehicleCommand

class PX4Commander(Node):
    def __init__(self):
        super().__init__('px4_commander')
        self.publisher = self.create_publisher(VehicleCommand, '/fmu/in/vehicle_command', 10)
        self.timer = self.create_timer(1.0, self.send_command)  # Send every second

    def send_command(self):
        msg = VehicleCommand()
        msg.timestamp = self.get_clock().now().nanoseconds // 1000  # Convert to microseconds
        msg.command = 22  # Command ID for ARM/DISARM
        msg.param1 = 1.0  # 1.0 = Arm, 0.0 = Disarm
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.publisher.publish(msg)
        self.get_logger().info("Sent ARM command to PX4")

def main(args=None):
    rclpy.init(args=args)
    node = PX4Commander()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()



##!/usr/bin/env python3
#
#import rclpy
#from rclpy.node import Node
#from std_msgs.msg import Float32
#import random
#
#
#class SensorPublisher(Node):
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
#def main(args=None):
#    rclpy.init(args=args)
#    sensor_publisher = SensorPublisher()
#    rclpy.spin(sensor_publisher)
#    sensor_publisher.destroy_node()
#    rclpy.shutdown()
#
#
#if __name__ == "__main__":
#    main()
