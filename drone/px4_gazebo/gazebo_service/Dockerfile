FROM osrf/ros:humble-desktop-full

RUN  --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update && apt-get install -y \
  iputils-ping \
  net-tools \
  tcpdump \ 
  wget \
  python3-pip \
  python3-venv \
  git 

RUN mkdir -p /root/simulation-gazebo

COPY . /root/simulation-gazebo

RUN chmod +x /root/simulation-gazebo/script_gz_sim.sh

RUN mkdir -p /root/.simulation-gazebo/worlds

WORKDIR /root/simulation-gazebo

RUN ./script_gz_sim.sh

RUN wget https://raw.githubusercontent.com/PX4/PX4-gazebo-models/main/simulation-gazebo

#RUN python simulation-gazebo --model_download_source --model_store /root/.simulation-gazebo

COPY drones_world.sdf /root/.simulation-gazebo/worlds

ENTRYPOINT ["/bin/bash", "-c"]
