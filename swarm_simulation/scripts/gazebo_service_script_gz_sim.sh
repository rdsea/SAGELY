#! /usr/bin/env bash

# check ubuntu version
# otherwise warn and point to docker?
UBUNTU_RELEASE="$(lsb_release -rs)"

if [[ "${UBUNTU_RELEASE}" == "14.04" ]]; then
  echo "Ubuntu 14.04 is no longer supported"
  exit 1
elif [[ "${UBUNTU_RELEASE}" == "16.04" ]]; then
  echo "Ubuntu 16.04 is no longer supported"
  exit 1
elif [[ "${UBUNTU_RELEASE}" == "18.04" ]]; then
  echo "Ubuntu 18.04"
elif [[ "${UBUNTU_RELEASE}" == "20.04" ]]; then
  echo "Ubuntu 20.04"
elif [[ "${UBUNTU_RELEASE}" == "22.04" ]]; then
  echo "Ubuntu 22.04"
fi

# Gazebo / Gazebo classic installation
if [[ "${UBUNTU_RELEASE}" == "22.04" ]]; then
  echo "Gazebo (Garden) will be installed"
  echo "Earlier versions will be removed"
  # Add Gazebo binary repository
  sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list >/dev/null
  sudo apt-get update -y --quiet

  # Install Gazebo
  gazebo_packages="gz-garden"
else
  sudo sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'
  wget http://packages.osrfoundation.org/gazebo.key -O - | sudo apt-key add -
  # Update list, since new gazebo-stable.list has been added
  sudo apt-get update -y --quiet

  # Install Gazebo classic
  if [[ "${UBUNTU_RELEASE}" == "18.04" ]]; then
    gazebo_classic_version=9
    gazebo_packages="gazebo$gazebo_classic_version libgazebo$gazebo_classic_version-dev"
  else
    # default and Ubuntu 20.04
    gazebo_classic_version=11
    gazebo_packages="gazebo$gazebo_classic_version libgazebo$gazebo_classic_version-dev"
  fi
fi

sudo DEBIAN_FRONTEND=noninteractive apt-get -y --quiet --no-install-recommends install \
  dmidecode \
  $gazebo_packages \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  libeigen3-dev \
  libgstreamer-plugins-base1.0-dev \
  libimage-exiftool-perl \
  libopencv-dev \
  libxml2-utils \
  pkg-config \
  protobuf-compiler \
  ;
