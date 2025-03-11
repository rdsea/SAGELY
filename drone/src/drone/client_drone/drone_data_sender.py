import rclpy
from rclpy.node import Node
import requests
import json

from std_msgs.msg import String  # Example message type, you may need to adjust


class DroneDataSender(Node):
    def __init__(self):
        super().__init__("drone_data_sender")
        self.subscription = self.create_subscription(
            String,
            "my_topic",  # Replace with the topic you are interested in
            self.listener_callback,
            10,
        )
        self.subscription  # Prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f"Received message: {msg.data}")
        self.send_data_to_server(msg.data, server_url)

    def send_data_to_server(self, data, server_url):
        # server_url = "http://192.168.49.2/endpoint"  # Replace with actual endpoint
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            server_url, headers=headers, data=json.dumps({"data": data})
        )
        self.get_logger().info(
            f"Response from server: {response.status_code}, {response.text}"
        )


def main(args=None):
    rclpy.init(args=args)
    drone_data_sender = DroneDataSender()
    rclpy.spin(drone_data_sender)
    drone_data_sender.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
