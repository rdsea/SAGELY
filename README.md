# SAGELY - SwArm-edGE PoLicY

[IEEE ICWS 2025](https://research.aalto.fi/en/publications/sagely-context-aware-holistic-service-policy-enforcement-across-s)

**Table of Contents**

- [Repo structure](#repo-structure)
- [Reproduce the ICWS experiment](#reproduce-the-icws-experiment)
  - [Creating the edge cluster](#creating-the-edge-cluster)
  - [Deploying the application](#deploying-the-application)
  - [Start swarm simulation](#start-swarm-simulation)
  - [Start the experiment](#start-the-experiment)
- [Citation](#citation)

## Repo structure

The repo contains 3 main parts:

- Swarm simulation part using [Gazebo](https://github.com/gazebosim/gz-sim) and [PX4](https://github.com/PX4/PX4-Autopilot)
- [SAGELY framework](./src/sagely/)
- [Applications](./applications/object_classification) with [utility](./infrastructure/) to set up the edge cluster infrastructure

## Reproduce the ICWS experiment

### Creating the edge cluster

1. Create a Kubernetes cluster using your chosen distribution, can be k3s, k8s, or kind for development like following:

```bash
kind create cluster --config ./infrastructure/kind-config.yaml
```

2. Deploy Istio and other necessary services:

```bash
./infrastructure/deploy_istio.sh
```

### Deploying the application

Firstly you need to update the submodule first using

```bash
git submodule update --init --recursive
```

Deploy the object classification application

```bash
cd ./applications/object_classification/deployment/edge/
./apply.sh
```

### Start swarm simulation

1. Navigate to the `drone/px4_gazebo` directory:

```bash
cd drone/px4_gazebo
```

2. Run the simulation gazebo server:

```bash
python ./gazebo_service/simulation-gazebo --gz_partition relay --gz_ip 192.168.132.1 --world drones_world
```

3. In another terminal, start the drones using the provided script:

```bash
./docker-compose-Adrone.sh
```

This will generate `docker-compose-drone-xxx.yml` files. Then, you need to start each drone in a separate terminal:

```bash
for ((i=101; i<=104; i++)); do
  docker-compose -f docker-compose-drone_$i.yml up -d
done
```

### Start the experiment

Navigate to the `experiments/ICWS` directory and run the experiment script with the desired policy and configuration.

The policy files used in the experiment (e.g., `rego_3kb_1.rego`, `rego_30kb_1.rego`, `rego_300kb_1.rego`) are provided in the `policy` directory. You can also generate your own policy files using the [generate_policy.py](./experiments/ICWS/policy/generate_policy.py)

For example, to run the experiment with a 3kb policy and 4 services:

```bash
cd experiments/ICWS
python3 ./run_experiment.py ./policy/rego_3kb_1.rego ./policy/rego_3kb_2.rego 0.5 4 3
```

To run all experiments, you can use the provided shell script:

```bash
./run_all_experiment.sh
```

This will create a new directory named `resultX` (where X is a number) and store the CSV results of the experiment in it.


# Basic example
## Infrastructure
### Minikube
- for a simple testing with minikube
  - infrastructure/
> tilt -f Tiltfile  up

### UAV swarm

#### Etcd-based UAV swarm
- An example for UAV swarm with docker containers
  - swarm_simulation/src/client_drone/

> docker build -t <TAG> -f Dockerfile.humble ../.. # E.g., docker build -t hongtringuyen/ros2_humble_drone  -f Dockerfile.humble ../.. 

- Create a docker-compose file or use an example from that directory
  - edit <TAG> for container name
  - image path for [object classification](/applications/object_classification/README.md)
    - carefully check **HEADER of requests**
  - check swarm_simulation/config/client_config.yaml
> docker compose -f docker-compose.yml up

- logs/ collects logs from drones

## Change policy for the cluster
- Apply a new rego policy to the cluster 
  - at src/sagely/policy_controlplane/policy_enforcer/
> edge_policy_enforcer.py [-h] [--configmap CONFIGMAP] [--key KEY] rego_path 

- Example
> python edge_policy_enforcer.py ../policy_templates/new_policy.rego

### Gazebo with UAV swarm
- Start Gazebo
> python simulation-gazebo --gz_partition relay --gz_ip 192.168.132.1 --world drones_world 

- Fill in basic setting in docker-compose-Adrone.sh
```bash
GZ_PARTITION="relay"
GZ_IP="192.168.132.1"
DRONE_MODEL="gz_x500"
PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7"
START_IP=101
END_IP=104
BASE_IP="192.168."
SWARM_SUBNET=132
CONTAINER=gazebo_sim_px4_ros2
SWARM_CONTAINER=<TAG>
ROS2_CONTAINER=ros:humble-ros-base-jammy
NETWORK_NAME=swarm_net # docker-based network
OPA_POLICY="./opa/policy.rego"
```

#TODO: need to check opa and envoy plugin
> ./docker-compose-Adrone.sh


## Citation

```bibtex
@inproceedings{nguyen_2025_sagely,
title = "SAGELY - Context-aware Holistic Service Policy Enforcement across Swarm-Edge Continuum",
keywords = "Continuum service-based application, Service-oriented computing, Policy-as-code, Policy enforcement, Swarm-edge-cloud computing",
author = "Hong-Tri Nguyen and Liang Yuan and Anh-Dung Nguyen and M. Ali Babar and Linh Truong",
booktitle = "IEEE International Conference on Web Services (ICWS 2025)",
publisher = "IEEE",
note = "IEEE International Conference on Web Services, ICWS ; Conference date: 07-07-2025 Through 12-07-2025",
}
```
