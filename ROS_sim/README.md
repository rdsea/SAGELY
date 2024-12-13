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

docker run --network host -v <image_data_for_sending>:/root/client_drone/src/data/val_images --rm -it --name client_drone2 client_drone ./entrypoint_etcd.sh <drone_id> 

# DEBUG
#docker exec -it client_drone ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml
# docker rm -f $(docker ps -a --filter "name=^client_drone" --format "{{.ID}}")  # remove all clinet_drone docker

```
