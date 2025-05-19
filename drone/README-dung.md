# Drone simulation

## PX4 and Gazebo

- Currently we're using:
  - Ubuntu 22.04
  - PX4 1.15.3 which comes with gazebo 7 and gz sim

### Cloning the code and install dependencies

```bash
git clone -b release/1.15 --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive && \
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh && \
```

### Running

- The general architecture of our simulation is as following:

  - World simulation using [Gazebo](https://gazebosim.org/home)
  - Flight software stack simulation using [PX4-Autopilot](https://github.com/PX4/PX4-Autopilot) and will be called SITL
  - Model of the vehicle is created by Gazebo and Gazebo will send the data to SITL through MAVLink set up

- We can start the SITL and Gazebo standalone or together:

  - Together:

  ```bash
  cd /path/to/PX4-Autopilot
  make px4_sitl gz_x500
  ```

  - Standalone:

  ```bash
  # Gazebo
  git clone https://github.com/PX4/PX4-gazebo-models.git
  python /path/to/Px4-gazebo-models/simulation-gazebo --world default_drone
  #NOTE: default_drone is taken from https://github.com/monemati/PX4-ROS2-Gazebo-YOLOv8/tree/main and we have a local version at drone/px4_gazebo/drones_world.sdf. Copy it to $HOME/.simulation-gazebo/worlds

  # PX4
  cd /path/to/PX4-Autopilot
  PX4_GZ_STANDALONE=1 make px4_sitl gz_x500
  ```

  - Or run the GZ headless (without GUI) to save resources:

  ```bash
  cd /path/to/PX4-Autopilot
  HEADLESS=1 make px4_sitl gz_x500
  ```

- Environment variable to control PX4 and GZ that we're using:

| Environment Variable            | Description                                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `PX4_SYS_AUTOSTART` (Mandatory) | Sets the airframe autostart ID of the PX4 airframe to start.                                                                       |
| `PX4_GZ_MODEL_NAME`             | Sets the name of an existing model in the Gazebo simulation. Mutually exclusive with `PX4_SIM_MODEL`.                              |
| `PX4_SIM_MODEL`                 | Sets the name of a new Gazebo model to be spawned. Mutually exclusive with `PX4_GZ_MODEL_NAME`.                                    |
| `PX4_GZ_MODEL_POSE`             | Sets the spawn position and orientation when using `PX4_SIM_MODEL`. Syntax: `"x,y,z,roll,pitch,yaw"`. Defaults to `[0,0,0,0,0,0]`. |
| `PX4_GZ_WORLD`                  | Sets the Gazebo world file. Ignored if a simulation is already running. Can be overridden.                                         |
| `PX4_GZ_PLATFORM_VEL`           | (When using a moving platform world) Sets the platform speed in m/s.                                                               |
| `PX4_GZ_PLATFORM_HEADING_DEG`   | (When using a moving platform world) Sets the platform heading (0° = east, CCW positive).                                          |
| `PX4_SIMULATOR=GZ`              | Sets the simulator to `gz` (required for Gazebo). Not always needed if set in the airframe.                                        |
| `PX4_GZ_STANDALONE`             | Prevents PX4 from launching Gazebo; use in standalone mode.                                                                        |
| `PX4_GZ_SIM_RENDER_ENGINE`      | Sets the render engine for Gazebo. Use `ogre` to fall back to OGRE 1 if issues occur.                                              |
| `PX4_SIM_SPEED_FACTOR`          | Sets the simulation speed factor (e.g., faster or slower than real time).                                                          |
| `PX4_GZ_FOLLOW_OFFSET_X`        | Sets follow camera X-axis offset from vehicle.                                                                                     |
| `PX4_GZ_FOLLOW_OFFSET_Y`        | Sets follow camera Y-axis offset from vehicle.                                                                                     |
| `PX4_GZ_FOLLOW_OFFSET_Z`        | Sets follow camera Z-axis offset from vehicle.                                                                                     |
| `GZ_IP`                         | IP of where GZ is run                                                                                                              |
| `GZ_RELAY`                      | ...                                                                                                                                |
| `GZ_PARITION`                   | ...                                                                                                                                |

- For example, here is a command that we usually run:

```bash
PX4_GZ_MODEL_POSE="268.08,-128.22,3.86,0.00,0,-0.7" PX4_GZ_STANDALONE=1 make px4_sitl gz_x500
```
