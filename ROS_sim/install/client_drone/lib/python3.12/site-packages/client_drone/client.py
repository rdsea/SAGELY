import rclpy
from rclpy.node import Node
import requests

class ClientNode(Node):
    def __init__(self):
        super().__init__('client_node')
        self.server_url = 'http://localhost:8000/tri'  # Update with your Flask server URL

    def send_request(self):
        try:
            response = requests.get(self.server_url)
            if response.status_code == 200:
                self.get_logger().info(f'Response: {response.content.decode()}')
            else:
                self.get_logger().info(f'Failed to reach server. Status code: {response.status_code}')
        except requests.exceptions.RequestException as e:
            self.get_logger().info(f'Request failed: {str(e)}')

def main(args=None):
    rclpy.init(args=args)

    client_node = ClientNode()
    client_node.send_request()

    client_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

