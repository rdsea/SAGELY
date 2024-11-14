import rclpy
from rclpy.node import Node
import requests
import yaml
import os
from threading import Timer
import random
import time

class ClientNode(Node):
    def __init__(self):
        super().__init__('client_node')
        self.declare_parameter('server_url', 'http://localhost:5010/preprocessing')  # Default value
        self.declare_parameter('ds_path','../../../../object_classification/src/artifact/dataset/imagenet/data/val_images')
        self.declare_parameter('rate',10)

        #self.server_url = self.get_parameter('server_url').get_parameter_value().string_value
        self.declare_parameter('yaml_file', 'client_drone.yaml')  # Default YAML file
        self.yaml_file = self.get_parameter('yaml_file').get_parameter_value().string_value

        self.gps_data = None
        self.image_paths = []

        self.load_yaml_data()

    def load_yaml_data(self):
        self.get_logger().info(f'Current working directory: {os.getcwd()}')
        if os.path.exists(self.yaml_file):
            with open(self.yaml_file, 'r') as file:
                data = yaml.safe_load(file)

                self.device_id = data.get('device_id', '')
                self.server_url = data.get('server_url', 'http://localhost:5010/preprocessing')
                #self.gps_data = data.get('gps_data', {} )
                self.ds_path = data.get('ds_path', '../../../../object_classification/src/artifact/dataset/imagenet/data/val_images')
                #self.image_paths = data.get('image_paths', [])
                self.rate = data.get('rate', 1)
                self.get_logger().info(f'Loaded ds_path data: {self.ds_path}')
                self.get_logger().info(f'Loaded rate: {self.rate}')
        else:
            self.get_logger().error(f'YAML file {self.yaml_file} does not exist')


    def send_request(self, url, requesting_interval, jpeg_images_list):
        timer = Timer(
            requesting_interval,
            self.send_request,
            args=(
                url,
                requesting_interval,
                jpeg_images_list,
            ),
        )
        timer.start()

        random_image = random.choice(jpeg_images_list)
        image_path = os.path.join(self.ds_path, random_image)

        # Extract the synset_id from the file name
        root, _ = os.path.splitext(image_path)
        _, synset_id = os.path.basename(root).rsplit("_", 1)

        # Open the image file as binary
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()

        start_time = time.time()
        file = {"file": ("random_image", img_data, "image/jpeg")}
        response = requests.post(url, files=file)
        print(response.json(), synset_id, (time.time() - start_time) * 1000)


    def main_send_request(self):

        device_id = self.device_id
        ds_path = self.ds_path
        req_rate = self.rate
        url = self.server_url

        files = os.listdir(ds_path)
        jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
        requesting_interval = 1.0 / req_rate

        timer = Timer(
            requesting_interval,
            self.send_request,
            args=(
                url,
                requesting_interval,
                jpeg_images_list,
            ),
        )
        timer.start()

def main(args=None):
    rclpy.init(args=args)

    client_node = ClientNode()
    client_node.main_send_request()

    client_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
