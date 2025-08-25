import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64
import random


class NumberPublisher(Node):
    def __init__(self):
        super().__init__("number_publisher")

        # DDS publisher
        self.publisher_ = self.create_publisher(Float64, "number_data", 10)
        self.timer_ = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        # Generate random number between 0 and 100
        number = random.uniform(0.0, 100.0)

        # Publish the number using DDS
        msg = Float64()
        msg.data = number
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published number: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = NumberPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
