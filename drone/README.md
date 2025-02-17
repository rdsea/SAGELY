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
# debug mode insde the docker
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
