# Use the official ROS2 base image base including developing tools
FROM ros:humble-ros-base-jammy
# desktop with GUI
#FROM osrf/ros:humble-desktop-full

# Install necessary packages
RUN  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update && apt-get install -y \
  iputils-ping \
  net-tools \
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
  ruby \
  tmuxinator

WORKDIR /root

# edit the script starting 
COPY . /root

# Install PX4
RUN cd /root && \
    git clone -b v1.15.4 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
    bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
    cp ./px4-rc.mavlink PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/ && \
    cd PX4-Autopilot && \
    PX4_GZ_STANDALONE=1 make px4_sitl

# Setup Micro XRCE-DDS Agent & Client
RUN cd /root && \
    git clone --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git && \
    cd Micro-XRCE-DDS-Agent && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install && \
    ldconfig /usr/local/lib/

RUN mkdir -p /root/ws_sensor_combined/src && \
    cd /root/ws_sensor_combined/src && \
    git clone --depth 1 https://github.com/PX4/px4_msgs.git && \
    git clone --depth 1 https://github.com/PX4/px4_ros_com.git && \
    /bin/bash -c "source /opt/ros/humble/setup.bash && cd /root/ws_sensor_combined && colcon build"


# RUN pip install requests etcd3 pydantic
# Build the workspace
# RUN /bin/bash -c "source /root/ws_sensor_combined/install/setup.bash"
# RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"
RUN echo "source /root/ws_sensor_combined/install/setup.bash" >> /root/.bashrc && \
    echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc 

# ROS2 tasks --  Create and build workspace
RUN mkdir -p /root/drone/src/data

# # Copy the package into the workspace
COPY . /root/drone/src/object_classification

# # Set the working directory
WORKDIR /root/drone/src/object_classification

RUN colcon build

# etcd3 -- skip from now
#RUN chmod +x scripts/trigger_request.sh

# generate a yml file to run
WORKDIR /root/PX4-Autopilot

# # Make script executable
# RUN chmod +x generate_yaml.sh
#
# # Generate YAML at build time
# RUN ./generate_yaml.sh

# Set up tmuxinator
RUN echo "export PATH=\$PATH:/root/.local/bin" >> /root/.bashrc

RUN mkdir -p /root/.config/tmuxinator/
# Set default command to start tmuxinator
#CMD ["tmuxinator", "start", "ros2_px4_gazebo"]

ENTRYPOINT ["/bin/bash", "-c"]
