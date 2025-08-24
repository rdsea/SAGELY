# Drone Simulation Documentation

This document provides a comprehensive overview of the drone simulation setup, including PX4, Gazebo, and ROS integration.

---

## PX4 and Gazebo Simulation

This section covers the basic setup and execution of the PX4 and Gazebo simulation environment.

### Cloning the code and install dependencies

```bash
git clone -b release/1.15 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
```

### Running

- The general architecture of our simulation is as following:

  - World simulation using [Gazebo](https://gazebosim.org/home)
  - Flight software stack simulation using [PX4-Autopilot](https://github.com/PX4/PX4-Autopilot) and will be called SITL
  - Model of the vehicle is created by Gazebo and Gazebo will send the data to SITL through MAVLink set up

- We can start the SITL and Gazebo standalone or together:

  - Together:

  ```bash
  cd /path/to/PX4-Autopilot
  make px4_sitl gz_x500
  ```

  - Standalone:

  ```bash
  # Gazebo
  git clone https://github.com/PX4/PX4-gazebo-models.git
  python /path/to/Px4-gazebo-models/simulation-gazebo --world default_drone
  #NOTE: default_drone is taken from https://github.com/monemati/PX4-ROS2-Gazebo-YOLOv8/tree/main and we have a local version at drone/px4_gazebo/drones_world.sdf. Copy it to $HOME/.simulation-gazebo/worlds

  # PX4
  cd /path/to/PX4-Autopilot
  PX4_GZ_STANDALONE=1 make px4_sitl gz_x500
  ```

  - Or run the GZ headless (without GUI) to save resources:

  ```bash
  cd /path/to/PX4-Autopilot
  HEADLESS=1 make px4_sitl gz_x500
  ```

- Environment variable to control PX4 and GZ that we're using:

| Environment Variable            | Description                                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `PX4_SYS_AUTOSTART` (Mandatory) | Sets the airframe autostart ID of the PX4 airframe to start.                                                                       |
| `PX4_GZ_MODEL_NAME`             | Sets the name of an existing model in the Gazebo simulation. Mutually exclusive with `PX4_SIM_MODEL`.                              |
| `PX4_SIM_MODEL`                 | Sets the name of a new Gazebo model to be spawned. Mutually exclusive with `PX4_GZ_MODEL_NAME`.                                    |
| `PX4_GZ_MODEL_POSE`             | Sets the spawn position and orientation when using `PX4_SIM_MODEL`. Syntax: "x,y,z,roll,pitch,yaw". Defaults to `[0,0,0,0,0,0]`. |
| `PX4_GZ_WORLD`                  | Sets the Gazebo world file. Ignored if a simulation is already running. Can be overridden.                                         |
| `PX4_GZ_PLATFORM_VEL`           | (When using a moving platform world) Sets the platform speed in m/s.                                                               |
| `PX4_GZ_PLATFORM_HEADING_DEG`   | (When using a moving platform world) Sets the platform heading (0° = east, CCW positive).                                          |
| `PX4_SIMULATOR=GZ`              | Sets the simulator to `gz` (required for Gazebo). Not always needed if set in the airframe.                                        |
| `PX4_GZ_STANDALONE`             | Prevents PX4 from launching Gazebo; use in standalone mode.                                                                        |
| `PX4_GZ_SIM_RENDER_ENGINE`      | Sets the render engine for Gazebo. Use `ogre` to fall back to OGRE 1 if issues occur.                                              |
| `PX4_SIM_SPEED_FACTOR`          | Sets the simulation speed factor (e.g., faster or slower than real time).                                                          |
| `PX4_GZ_FOLLOW_OFFSET_X`        | Sets follow camera X-axis offset from vehicle.                                                                                     |
| `PX4_GZ_FOLLOW_OFFSET_Y`        | Sets follow camera Y-axis offset from vehicle.                                                                                     |
| `PX4_GZ_FOLLOW_OFFSET_Z`        | Sets follow camera Z-axis offset from vehicle.                                                                                     |
| `GZ_IP`                         | IP of where GZ is run                                                                                                              |
| `GZ_RELAY`                      | ...                                                                                                                                |
| `GZ_PARITION`                   | ...                                                                                                                                |

- For example, here is a command that we usually run:

```bash
PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 make px4_sitl gz_x500
```

### Drone show

1. Create drone in each docker instance with `startup_sitl.sh`

- Change `MAV_SYS_ID`

- Set position with respect to `config.csv`

2. Coordination using `coordination.py`

---

## Multi-PX4 Gazebo Setup

This section details the setup for running a Gazebo simulation with multiple PX4 instances.

The most errors from the connection between PX4 and Gazebo

- Ubuntu 22.04
- PX4 1.5
- install gazebo via px4/tools/setup
  - Gazebo 7.9
  - gz sim (gazebo-garden)

### Errors

> ekf2 missing data is the conflict data from gazebo 7.9 and 8.9 between px4 and gazebo (on 2 machines)

compass missing data is the issues from NavSat

> <plugin name="gz::sim::systems::NavSat" filename="gz-sim-navsat-system"/>

### Network setting for a single machine working via a docker network (that can improve to docker-compose or k8s-based)

```bash
# create a network 192.168.1.0/24 called px4net
docker network create \
  --driver=bridge \
  --subnet=192.168.132.0/24 px4net
```

### GAZEBO and PX4

Gazebo version 7.9 and PX4 version **1.15**

May have a

#### GAZEBO

.
├── ~/.simulation-gazebo/ OR PX4-Autopilot/Tool/simulation
│   ├─ Models
│   ├─ world/default.sdf

> git clone <https://github.com/PX4/PX4-gazebo-models.git>

```bash
python simulation-gazebo --overwrite # to download models and worlds
python simulation-gazebo --gz_partition <name_of_gaezbo> --gz_ip <IP_of_gazebo> --world default_drone

#Example
python /path/to/simulation-gazebo --gz_partition relay --gz_ip 192.168.1.1 --world default_drone
```

#### PX4

```bash
# setting px4 1.15
git clone -b release/1.15 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
cd PX4-Autopilot && \
make px4_sitl

pip install mavsdk

GZ_PARTITION=<name_of_gaezbo> GZ_RELAY=<IP_of_gazebo> GZ_IP=<IP_of_currentPX4> PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i <id_of_currentPX4>

# Example
# Start a docker with the IP in the network we set
# docker run -it --rm --name=px4-drone1 --net px4net --ip 192.168.1.101 px4_graze /bin/bash

GZ_PARTITION=relay GZ_RELAY=192.168.1.1 GZ_IP=192.168.1.101 PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_WORLD=default_drone ./build/px4_sitl_default/bin/px4 -i 1

 ./build/px4_sitl_default/bin/px4 -i 1
```

add this line of code to the rcS

- param set-default SENS_IMU_MODE 0

### Docker setting

Create a virtual network and setting with drones 
- edit docker-compose-Adrone.sh
- output is docker-compose-drone-xxx.yml where xxx is drone name 
```bash
# Base details
GZ_PARTITION="relay"
GZ_IP="192.168.132.1" # IP gazebo server
DRONE_MODEL="gz_x500" # drone model
PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" # position of drones in the world

START_IP=101 # start and end of drone IP and their network
END_IP=104
BASE_IP="192.168."
SWARM_SUBNET=132 # swarm network conenct to gazebo network

CONTAINER=hongtringuyen/gazebo_sim_px4 # container gazebo client, PX4 to allow connecting with gazebo server

SWARM_CONTAINER=hello-world # container working among drone swarm
# application services
ROS2_CONTAINER=ros:humble-ros-base-jammy # ros2 service run on top of the setting

NETWORK_NAME=swarm_net # network name for the swarm

OPA_POLICY="./opa/policy.rego" # directory of the policy for loading
```

Run simulation gazebo server
```bash
python ./gazebo_service/simulation-gazebo --gz_partition relay --gz_ip 192.168.132.1 --world drones_world
```

Run keyboard to control the drone (only one drone), can use [QGroundControl](https://qgroundcontrol.com/) to control more drones
```bash
python ./keyboard_control/keyboard-mavsdk-test.py 
```

Clean all everything
```bash
./cleaning.sh
```

---

## ROS2 and PX4 Integration

This section explains how to integrate ROS2 with the PX4 simulation.

- We're using ROS2 humble
- PX4 use micro-ROS to communicate with ROS2
- We need to install `micro-ros-agent` and `micro-ros-setup`

```bash
# Source the ROS 2 installation
source /opt/ros/humble/setup.bash
# Create a workspace and download the micro-ROS tools
mkdir -p microros_ws
cd microros_ws
git clone -b $ROS_DISTRO https://github.com/micro-ROS/micro_ros_setup.git
src
# Update dependencies
rosdep update && rosdep install --from-paths src --ignore-src -y
# Build micro-ROS tools and source them
colcon build
source install/local_setup.bash
```

- To connect ROS2 with PX4, we need to create a micro-ROS agent

```bash
# Download micro-ROS-Agent packages
ros2 run micro_ros_setup create_agent_ws.sh
# Build step
ros2 run micro_ros_setup build_agent.sh
# Source the installation
source install/local_setup.bash
```

- Run the agent

```bash
# UDPv4 connection example
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

- In PX4, we need to enable the micro-ROS client

```bash
make px4_sitl gz_x500
# In the PX4 console
microros_client start -t udp -i 127.0.0.1 -p 8888
```

- Now we can run ROS2 nodes to communicate with PX4

```bash
# For example, we can run a teleop node to control the drone
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

- We can also run a node to subscribe to the sensor data from PX4

```bash
# For example, we can run a node to subscribe to the IMU data
ros2 topic echo /fmu/out/vehicle_imu
```

- To make it easier, we can create a launch file to run all the nodes at once

```bash
# For example, we can create a launch file to run the micro-ROS agent, the teleop node, and the IMU subscriber node
<launch>
    <node pkg="micro_ros_agent" exec="micro_ros_agent" name="micro_ros_agent" output="screen"
        args="udp4 --port 8888"/>
    <node pkg="teleop_twist_keyboard" exec="teleop_twist_keyboard" name="teleop_twist_keyboard" output="screen"/>
    <node pkg="ros2" exec="topic" name="imu_subscriber" output="screen"
        args="echo /fmu/out/vehicle_imu"/>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with ROS2

```bash
# For example, we can run the following command to run the simulation with ROS2
ros2 launch ros2_px4_gazebo single_vehicle.launch.py
```

- We can also create our own launch file to run the simulation with our own world and models

```bash
# For example, we can create a launch file to run the simulation with our own world and models
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with multiple vehicles

```bash
# For example, we can run the following command to run the simulation with multiple vehicles
ros2 launch ros2_px4_gazebo multi_vehicle.launch.py
```

- We can also create our own launch file to run the simulation with multiple vehicles

```bash
# For example, we can create a launch file to run the simulation with multiple vehicles
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <group ns="drone1">
        <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
            <arg name="vehicle_model" value="your_model"/>
            <arg name="x" value="0"/>
            <arg name="y" value="0"/>
            <arg name="z" value="0"/>
        </include>
    </group>
    <group ns="drone2">
        <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
            <arg name="vehicle_model" value="your_model"/>
            <arg name="x" value="1"/>
            <arg name="y" value="1"/>
            <arg name="z" value="0"/>
        </include>
    </group>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with a joystick

```bash
# For example, we can run the following command to run the simulation with a joystick
ros2 launch ros2_px4_gazebo single_vehicle_joystick.launch.py
```

- We can also create our own launch file to run the simulation with a joystick

```bash
# For example, we can create a launch file to run the simulation with a joystick
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
    <node pkg="joy" exec="joy_node" name="joy_node" output="screen"/>
    <node pkg="teleop_twist_joy" exec="teleop_node" name="teleop_node" output="screen"/>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with a custom controller

```bash
# For example, we can run the following command to run the simulation with a custom controller
ros2 launch ros2_px4_gazebo single_vehicle_custom_controller.launch.py
```

- We can also create our own launch file to run the simulation with a custom controller

```bash
# For example, we can create a launch file to run the simulation with a custom controller
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
    <node pkg="your_package" exec="your_controller" name="your_controller" output="screen"/>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with a custom sensor

```bash
# For example, we can run the following command to run the simulation with a custom sensor
ros2 launch ros2_px4_gazebo single_vehicle_custom_sensor.launch.py
```

- We can also create our own launch file to run the simulation with a custom sensor

```bash
# For example, we can create a launch file to run the simulation with a custom sensor
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
    <node pkg="your_package" exec="your_sensor" name="your_sensor" output="screen"/>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with a custom payload

```bash
# For example, we can run the following command to run the simulation with a custom payload
ros2 launch ros2_px4_gazebo single_vehicle_custom_payload.launch.py
```

- We can also create our own launch file to run the simulation with a custom payload

```bash
# For example, we can create a launch file to run the simulation with a custom payload
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
    <node pkg="your_package" exec="your_payload" name="your_payload" output="screen"/>
</launch>
```

- Then we can run the launch file

```bash
ros2 launch <your_package> <your_launch_file>
```

- We can also use the `ros2_px4_gazebo` package to run the simulation with a custom mission

```bash
# For example, we can run the following command to run the simulation with a custom mission
ros2 launch ros2_px4_gazebo single_vehicle_custom_mission.launch.py
```

- We can also create our own launch file to run the simulation with a custom mission

```bash
# For example, we can create a launch file to run the simulation with a custom mission
<launch>
    <include file="$(find ros2_px4_gazebo)/launch/gz_sim.launch.py">
        <arg name="world" value="$(find your_package)/worlds/your_world.sdf"/>
    </include>
    <include file="$(find ros2_px4_gazebo)/launch/px4.launch.py">
        <arg name="vehicle_model" value="your_model"/>
    </include>
</launch>
```

---

## ROS and MAVLink Communication

This section covers ROS, MAVLink, and their interaction.

### Note for ROS

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

### different Test for etcd

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

### MicroXRCEAgent, ROS2, PX4, and MAVLink Setup

This guide outlines the steps to set up communication between a ROS2 node and PX4 using DDS (via Micro XRCE-DDS), and then forward the data to a GCS using MAVLink.

#### Steps

##### 2. Run ROS2 Publisher Node

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

##### 3. Run ROS2 DDS to MAVLink Forwarder Node

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

### Experiments via MAVLink here

#### 1. Start Micro XRCE-DDS Agent

Start the Micro XRCE-DDS Agent to handle DDS communication between ROS2 and PX4:

```sh
MicroXRCEAgent udp4 -p 8888
```

#### 4. Run PX4 SITL

Execute PX4 SITL to run its own PX4 device:

```bash
cd <path-to-PX4>/build/px4_sitl_default/bin
./px4 # make px4_sitl_default gazebo
```

#### 5. Configure PX4 to Forward MAVLink Messages

Run the following commands in the PX4 console to forward messages:

```bash
# in the px4 shell
mavlink stop-all
#mavlink start -u 14550 -o 14551 -t 127.0.0.1 -x -f

# command to forward from 14550 to 14551 outside ROS2 machine to client
mavlink start -u 14550 -o 14553 -t 130.233.195.206 -x -f

# command to forward from 14560 outside to 14561 inside ROS2 machine
mavlink start -u 14560 -o 14561 -t 127.0.0.1 -x -f
```

This configuration forwards the port 14550 to 14551 (from ROS2 to GCS port).

This configuration forwards the port 14560 to 14561 (from GCS port to ROS2).

```

This configuration forwards the port 14550 to 14551 (GCS port).

```

# copy receive_FTP to the client_drone

scp receive_FTP.py drone0:/root/drone/src/object_classification/client_drone

# before running

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
````

#### 6. Run GCS Script

This script listens on port 14551 and prints the received MAVLink messages:

```bash
python3 gcs_setting2.py
````

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
