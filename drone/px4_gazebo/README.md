# A setting for a gezebo with multi-px4

# How to build Docker container

## 1. Config the Dockerfile according to your needs.

You need to have a correlative version between ROS, Ubuntu, Gazebo, PX4. 
The default right now is
| Software    | Version |
| -------- | ------- |
| ROS2  | Jazzy   |
| Ubuntu | Noble     |
| PX4    | 1.16    |
| Gazebo simulation    | 8.9.0 |

- For ROS2 and ubuntu since the version are tied together, you need to change the first line of the [Dockerfile](../px4_gazebo/px4_drone/Dockerfile) to match your ROS2 and Ubuntu version.
`` FROM ros:jazzy-ros-base-noble `` ex. for jammmy (ROS2) and jammy(Ubuntu 22.04) you can use ``FROM ros:humble-ros-base-jammy``
you also need to change ROS version in the following places
`` /bin/bash -c "source /opt/ros/${YOUR_ROS_VERSION}/setup.bash && cd /root/ws_sensor_combined && colcon build" ``
`` echo "source /opt/ros/${YOUR_ROS_VERSION}/setup.bash" >> /root/.bashrc ``

- For PX4, you need to change the PX4 version in the [Dockerfile](../px4_gazebo/px4_drone/Dockerfile) to match your PX4 version. The default is 1.16, so you can change it to 1.15 by changing ``git clone -b ${YOUR_PX4_VERSION} --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && ``

- For Gazebo simulation, you need to have the right version of Gazebo installed. You can see what version of Gazebo you have installed by running the following command: ``gz sim --versions``

Then you can build the docker image with the following command:

```bash
docker build -t px4_gazebo:latest .
```

#### or you can download the pre-built docker image from Docker Hub

```bash
docker pull korawitrupanya/px4_gazebo_ros2_yolo8:latest
```

### 2. Run the Gazebo simulation server

There are two ways to run the Gazebo simulation server, either by using the PX4-Autopilot/Tool/simulation or by using the simulation-gazebo script.
1. To use PX4-Autopilot/Tool/simulation. Assuming you have already cloned the PX4-Autopilot repository(``git clone -b ${YOUR_PX4_VERSION} --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && ``) You will have to go to the following path in the PX4-Autopilot

```
PX4-Autopilot
├── Tool
│   ├── simulation
│       ├──gz
│         ├──simulation-gazebo

```

 you can run the following command:

```bash
python simulation-gazebo --overwrite # to download models and worlds
python simulation-gazebo --gz_partition <name_of_gaezbo> --gz_ip <IP_of_gazebo> --world default_drone

#Example
python /path/to/simulation-gazebo --gz_partition relay --gz_ip 192.168.1.1 --world default_drone
```

2. To use the simulation-gazebo script, you will need to clone the px4 gazebo repository and run the following command:
``git clone https://github.com/PX4/PX4-gazebo-models`` and you can run the similar command as above or just follow the README instructions of the repository.

## 3. Config number of Drones you want to use
You will need to adjust `` END_IP `` number in [generate-drone-docker.sh](../px4_gazebo/generate-drone-docker.sh) to the number of drones you want to use. The default is 4 drones, so for example you can change it to 10 drones by changing `` END_IP=104 `` and `` START_IP=101 `` to `` END_IP=110 `` and `` START_IP=101 ``.

## Example of configuration of script file
- edit [generate-drone-docker.sh](../px4_gazebo/generate-drone-docker.sh)
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

Then you should be able to run the script to generate the docker-compose files for each drone.

## Errors
> ekf2 missing data is the conflict data from gazebo 7.9 and 8.9 between px4 and gazebo (on 2 machines)

compass missing data is the issues from NavSat
`` <plugin name="gz::sim::systems::NavSat" filename="gz-sim-navsat-system"/> ``