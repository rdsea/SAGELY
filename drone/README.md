# Note for ROS 

### Install ROS iron
- ROS supports
  - networking for remote and connect among robots


### Rosdep to manage dependencies
> rosdep install -i --from-path src --rosdistro iron -y

- Colon to build package
  - build
  - Install
  - log
  - src

# 
```bash

cd src/client_drone

docker build -t client_drone . 

# Download etcd version 3.5
# let the etcd and etcdctl in src/client_drone/clinet_drone

docker run --network host -v <image_data_for_sending>:/root/client_drone/src/data/val_images --rm -it --name client_drone0 client_drone "./entrypoint_etcd.sh <drone_id>"

# DEBUG
#docker exec -it client_drone ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml
# docker rm -f $(docker ps -a --filter "name=^client_drone" --format "{{.ID}}")  # remove all clinet_drone docker

```

Test
```bash
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
