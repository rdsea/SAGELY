# A setting for a gezebo with multi-px4

The most errors from the connection between PX4 and Gazebo

- Ubuntu 22.04
- PX4 1.5
- install gazebo via px4/tools/setup
  - Gazebo 7.9
  - gz sim (gazebo-garden)

## Errors

> ekf2 missing data is the conflict data from gazebo 7.9 and 8.9 between px4 and gazebo (on 2 machines)

compass missing data is the issues from NavSat

> <plugin name="gz::sim::systems::NavSat" filename="gz-sim-navsat-system"/>

## Network setting for a single machine working via a docker network (that can improve to docker-compose or k8s-based)

```bash
# create a network 192.168.1.0/24 called px4net
docker network create \                                                                                                                      ─╯
  --driver=bridge \
  --subnet=192.168.132.0/24 px4net
```

## GAZEBO and PX4

Gazebo version 7.9 and PX4 version **1.15**

May have a

### GAZEBO

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

### PX4

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

## Docker setting

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
SWARM_SUBNET=132 # swarm network connect to gazebo network

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
