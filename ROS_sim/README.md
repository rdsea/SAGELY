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

docker run --network host -v <image_data_for_sending>:/root/client_drone/src/data/val_images --rm -it client_drone bash --

docker exec -it clinent_drone ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml
```
