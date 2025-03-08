# Note for ROS

```bash
.
├── client_drone
│   ├── client_config.yaml
│   ├── client_drone.yaml
│   ├── client.py
│   └── __init__.py
├── Dockerfile
├── package.xml
├── pyproject_.toml
├── requirements.txt
├── resource
│   └── client_drone
├── scripts
│   ├── entrypoint_etcd.sh
│   ├── etcd
│   ├── etcdctl
│   └── trigger_request.sh
├── setup.cfg
└── setup.py


# build docker
docker build -t drone_ros2 .
# debug mode inside the docker
docker run --rm -it drone_ros2  /bin/bash -c "echo 'Hello from Docker!'"
# Download etcd version 3.5 -- in docker can download and extract direct; however, to be ez I cp from my local directory to
# let the etcd and etcdctl in src/client_drone/clinet_drone
docker run --network host -v <image_data_for_sending>:/root/drone/src/data/val_images --rm -it --name client_drone0 client_drone "../script/entrypoint_etcd.sh <drone_id>"
#docker run --network host -v ~/holisticPolicy/object_classification/src/artifact/dataset/imagenet/data/val_images:/root/drone/src/data/val_images --rm -it --name drone0 drone_ros2 "../scripts/entrypoint_etcd.sh 0"

# DEBUG
#docker exec -it client_drone ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml
# docker rm -f $(docker ps -a --filter "name=^client_drone" --format "{{.ID}}")  # remove all clinet_drone docker

```

# different Test for etcd

```bash
# 3 nodes
export TOKEN=token-01
export CLUSTER_STATE=new
export NAME_0=drone_0
export NAME_1=drone_1
export NAME_2=drone_2
export HOST_0=0.0.0.0
export HOST_1=0.0.0.0
export HOST_2=0.0.0.0
export CLUSTER=${NAME_0}=http://${HOST_0}:2380,${NAME_1}=http://${HOST_1}:2381,${NAME_2}=http://${HOST_2}:2382
export THIS_NAME=${NAME_0}
export THIS_IP=${HOST_0}
export PEER_PORT=2380
export CLIENT_PORT=2379

./etcd --data-dir=data.etcd --name ${THIS_NAME} \
  --advertise-client-urls http://${THIS_IP}:${CLIENT_PORT} --listen-client-urls http://${THIS_IP}:${CLIENT_PORT} \
  --initial-advertise-peer-urls http://${THIS_IP}:${PEER_PORT} --listen-peer-urls http://${THIS_IP}:${PEER_PORT} \
  --initial-cluster ${CLUSTER} \
  --initial-cluster-state ${CLUSTER_STATE} --initial-cluster-token ${TOKEN} &


# single node
export TOKEN=token-01
export CLUSTER_STATE=new
export NAME_0=drone_0
export HOST=0.0.0.0
export PEER_PORT=2380
export CLIENT_PORT=2379
export THIS_NAME=${NAME_0}
export THIS_IP=${HOST}
export CLUSTER=${NAME_0}=http://${HOST_0}:2380,${NAME_1}=http://${HOST_1}:2381,${NAME_2}=http://${HOST_2}:2382

./etcd --data-dir=data.etcd --name ${THIS_NAME} \
  --advertise-client-urls http://${THIS_IP}:${CLIENT_PORT} --listen-client-urls http://${THIS_IP}:${CLIENT_PORT} \
  --initial-advertise-peer-urls http://${THIS_IP}:${PEER_PORT} --listen-peer-urls http://${THIS_IP}:${PEER_PORT} \
  --initial-cluster ${THIS_NAME}=http://${THIS_IP}:${PEER_PORT} \
  --initial-cluster-state new \
  --initial-cluster-token token-01 &

```

# MicroXRCEAgent, ROS2, PX4, and MAVLink Setup

This guide outlines the steps to set up communication between a ROS2 node and PX4 using DDS (via Micro XRCE-DDS), and then forward the data to a GCS using MAVLink.

## Steps

### 2. Run ROS2 Publisher Node

This node generates numerical data and publishes it via DDS:

```bash
ros2 run clinet_drone publisher
```

```python

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
```

### 3. Run ROS2 DDS to MAVLink Forwarder Node

This node subscribes to the DDS topic, converts the data to MAVLink format, and sends it to PX4 at udpout://127.0.0.1:14550:

```bash
ros2 run client_drone subscriber
```

```python

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2


class DDS2PX4Forwarder(Node):
    def __init__(self):
        super().__init__("dds2px4_forwarder")

        # MAVLink connection setup to PX4 (MAVLink instance on port 14550)
        self.mav = mavutil.mavlink_connection("udpout:127.0.0.1:14550")
        self.subscription = self.create_subscription(
            Float64, "number_data", self.listener_callback, 10
        )

    def listener_callback(self, msg):
        number = msg.data

        # Ensure time_boot_ms fits within valid range
        time_boot_ms = (self.get_clock().now().nanoseconds // 1000000) % 4294967296

        named_value_float = mavlink2.MAVLink_named_value_float_message(
            time_boot_ms=time_boot_ms,
            name=b"number",  # 10-character name identifier
            value=number,
        )
        try:
            self.mav.mav.send(named_value_float)
            self.get_logger().info(f"Sent number to PX4: {number}")
        except Exception as e:
            self.get_logger().error(f"Failed to send number: {str(e)}")


def main(args=None):
    rclpy.init(args=args)
    node = DDS2PX4Forwarder()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 1. Start Micro XRCE-DDS Agent

Start the Micro XRCE-DDS Agent to handle DDS communication between ROS2 and PX4:

```sh
MicroXRCEAgent udp4 -p 8888
```

### 4. Run PX4 SITL

Execute PX4 SITL to run its own PX4 device:

```bash
cd <path-to-PX4>/build/px4_sitl_default/bin
./px4 # make px4_sitl_default gazebo
```

### 5. Configure PX4 to Forward MAVLink Messages

Run the following commands in the PX4 console to forward messages:

```bash
# in the px4 shell
mavlink stop-all
#mavlink start -u 14550 -o 14551 -t 127.0.0.1 -x -f

mavlink start -u 14550 -o 14551 -t 130.233.195.206 -x -f

mavlink start -u 14560 -o 14561 -t 127.0.0.1 -x -f
```

This configuration forwards the port 14550 to 14551 (GCS port).

```
# copy receive_FTP to the client_drone
scp receive_FTP.py  drone0:/root/drone/src/object_classification/client_drone


source /opt/ros/humble/setup.bash
source /root/ws_sensor_combined/install/setup.bash
# compile
colcon build

# source
source install/setup.bash

# run
ros2 run client_drone receive_FTP

# send requests px4
scp ./experiments/policy_drone_test/send_FTP_px4.py jet6:/home/aaltosea/
```

### 6. Run GCS Script

This script listens on port 14551 and prints the received MAVLink messages:

```bash
python3 gcs_setting2.py
```

```python

from pymavlink import mavutil

# Create a connection to listen to MAVLink messages
conn = mavutil.mavlink_connection("udp:127.0.0.1:14551")

print("Waiting for MAVLink messages...")

while True:
    msg = conn.recv_match(blocking=True)
    if msg:
        msg_type = msg.get_type()
        if msg_type == "NAMED_VALUE_FLOAT":
            number_data = msg.value
            print(
                f"Received Named Value Float: {msg.name} = {number_data}"
            )
        else:
            print(f"Received MAVLink message: {msg_type}")
```

# GCS

```bash
pip install mavsdk
```
