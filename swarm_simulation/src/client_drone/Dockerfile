# Use the official ROS2 base image base including developing tools
#FROM ros:humble-ros-base-jammy
FROM ros:jazzy-ros-base-noble
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
  #python3-colcon-common-extensions \
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

#RUN apt-get update --fix-missing

# Install uv (adds to ~/.local/bin)
# --- Python toolchain + venv -------------------------------------------------
# Install uv (fast pip)
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# ENV PATH="/root/.local/bin:$PATH"
#
# # Create dedicated venv and prefer it globally
# RUN uv venv --python /usr/bin/python3 /opt/venv
# ENV VIRTUAL_ENV=/opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
# ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# ENV PYTHONNOUSERSITE=1
# # Force colcon's Python to the venv (makes console-script shebangs correct)
# ENV COLCON_PYTHON_EXECUTABLE=/opt/venv/bin/python3


# Install Python deps into the venv ONCE
# RUN --mount=type=cache,target=/root/.cache/uv \
#   uv pip install --upgrade pip setuptools wheel catkin_pkg empy && \
#   uv pip install --no-cache-dir \
#   requests \
#   pymavlink \
#   PyYAML \
#   aiohttp \
#   etcd3 \
#   pydantic

# ---------------- Python venv  -----------------
# RUN pip3 install setuptools wheel catkin_pkg empy 
# RUN pip3 install requests etcd3 pydantic
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install -U pip setuptools wheel colcon-common-extensions catkin_pkg empy \
  && pip install requests PyYAML aiohttp etcd3 pydantic pymavlink numpy
# --- PX4 (SITL) --------------------------------------------------------------
WORKDIR /root

# edit the script starting 
COPY config/px4-rc.mavlink /tmp/px4-rc.mavlink

# Install PX4
# RUN PIP_BREAK_SYSTEM_PACKAGES=1 bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
# RUN cd /root && \
#   #git clone -b v1.15.4 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
#   git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
#   bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
#   cp ./config/px4-rc.mavlink PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/ && \
#   cd PX4-Autopilot && \
#   PX4_GZ_STANDALONE=1 make px4_sitl

RUN git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
  bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
  cp /tmp/px4-rc.mavlink PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/ && \
  cd PX4-Autopilot && \
  PX4_GZ_STANDALONE=1 make -j"$(nproc)" px4_sitl

# --- Micro XRCE-DDS Agent ----------------------------------------------------
RUN git clone --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git && \
  cd Micro-XRCE-DDS-Agent && \
  mkdir build && cd build && \
  cmake .. && make -j"$(nproc)" && make install && ldconfig /usr/local/lib/


# # Setup Micro XRCE-DDS Agent & Client
# RUN cd /root && \
#   git clone --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git && \
#   cd Micro-XRCE-DDS-Agent && \
#   mkdir build && \
#   cd build && \
#   cmake .. && \
#   make && \
#   make install && \
#   ldconfig /usr/local/lib/

# --- px4_ros_com workspace ---------------------------------------------------
RUN mkdir -p /root/ws_sensor_combined/src && \
  cd /root/ws_sensor_combined/src && \
  git clone --depth 1 https://github.com/PX4/px4_msgs.git && \
  git clone --depth 1 https://github.com/PX4/px4_ros_com.git && \
  /bin/bash -c "source /opt/ros/jazzy/setup.bash && cd /root/ws_sensor_combined && colcon build"

# source /opt/ros/jazzy/setup.bash && \
# cd /root/ws_sensor_combined && colcon build --symlink-install

# RUN mkdir -p /root/ws_sensor_combined/src && \
#   cd /root/ws_sensor_combined/src && \
#   git clone --depth 1 https://github.com/PX4/px4_msgs.git && \
#   git clone --depth 1 https://github.com/PX4/px4_ros_com.git && \
#   /bin/bash -c "source /opt/ros/jazzy/setup.bash && cd /root/ws_sensor_combined && colcon build"

# --- Your ROS2 workspace -----------------------------------------------------
#RUN pip install requests etcd3 pydantic
RUN mkdir -p /root/drone/src/object_classification

COPY . /root/drone/src/object_classification

WORKDIR /root/drone/src/object_classification

# Build with venv python and ROS env, produce console scripts that use /opt/venv/bin/python3
RUN  /bin/bash -c "source /opt/ros/jazzy/setup.bash && colcon build"
#RUN source /opt/ros/jazzy/setup.bash && colcon build

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
  echo "source /root/ws_sensor_combined/install/setup.bash" >> /root/.bashrc && \
  echo "source /root/drone/src/object_classification/install/setup.bash" >> /root/.bashrc

# --- helper scripts + etcd binaries -----------------------------------------
RUN chmod +x /root/drone/src/object_classification/scripts/trigger_request.sh && \
  chmod +x /root/drone/src/object_classification/scripts/entrypoint_etcd.sh

# ROS2 tasks --  Create and build workspace
RUN mkdir -p /root/drone/src/data

RUN wget -O /tmp/etcd.tar.gz https://github.com/etcd-io/etcd/releases/download/v3.6.0/etcd-v3.6.0-linux-amd64.tar.gz && \
  tar -xzvf /tmp/etcd.tar.gz -C scripts/ --strip-components=1 && \
  rm /tmp/etcd.tar.gz

WORKDIR /root/drone/src/object_classification/client_drone

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python



# Set up tmuxinator
RUN echo "export PATH=\$PATH:/root/.local/bin" >> /root/.bashrc

RUN mkdir -p /root/.config/tmuxinator/
# Set default command to start tmuxinator
CMD ["tmuxinator", "start", "ros2_px4_gazebo"]
