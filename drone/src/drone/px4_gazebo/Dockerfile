# Use the official ROS2 base image
FROM ros:humble-ros-core-jammy

# Install necessary packages
RUN  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update && apt-get install -y \
  tcpdump \ 
  vim \
  git \
  cmake \
  build-essential \
  python3-pip \
  python3-venv \
  python3-colcon-common-extensions \
  clang \
  lldb \
  ninja-build \
  libgtest-dev \
  libeigen3-dev \
  libopencv-dev \
  libyaml-dev \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-good \
  gstreamer1.0-tools \
  sudo \
  wget \
  curl \
  tmux \
  ruby 

WORKDIR /root

# Install PX4
RUN cd /root && \
    git clone -b release/1.15 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
    bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
    cd PX4-Autopilot && \
    make px4_sitl

ENTRYPOINT ["/bin/bash", "-c"]
#CMD ["ros2 run client_drone client --ros-args -p yaml_file:=client_drone.yaml"]
