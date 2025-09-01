#!/usr/bin/env python3

from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from pydantic import BaseModel, IPvAnyAddress, validator
from typing import Dict, List, Optional

import argparse

import subprocess
import os
# ... [Pydantic models GazeboConfig, DroneConfig, NetworkConfig, InputConfig here] ...


class GazeboConfig(BaseModel):
    gz_sim: bool = False
    gz_partition_name: str = "relay"
    gz_ip: Optional[IPvAnyAddress] = None  # <-- allow missing
    world_model: str
    px4_gz_model_pose: str = "268.08,-128.22,3.86,0.00,0,-0.7"

    @validator("px4_gz_model_pose")
    def validate_pose(cls, v):
        parts = v.split(",")
        if len(parts) != 6:
            raise ValueError("px4_gz_model_pose must have 6 comma-separated floats")
        return v


class DroneConfig(BaseModel):
    image: str
    start_ip: int
    end_ip: int
    drone_model: str = "gz_x500"
    opa_policy: str = "policy.rego"

    @validator("end_ip")
    def end_after_start(cls, v, values):
        if "start_ip" in values and v < values["start_ip"]:
            raise ValueError("end_ip must be >= start_ip")
        return v


# class NetworkConfig(BaseModel):
#     base_ip: str = "192.168."
#     swarm_subnet: int = 132
#     target_base_name: str = "swarm_net"
#     prefer_minikube: bool = True
#     tries: int = 200
class NetworkConfig(BaseModel):
    base_ip: str = "192.168."
    swarm_subnet: int = 132
    target_base_name: str = "swarm_net"
    prefer_minikube: bool = True
    tries: int = 200


class InputConfig(BaseModel):
    gazebo: GazeboConfig
    drone: DroneConfig
    network: NetworkConfig


def load_config(path: str) -> InputConfig:
    data = yaml.safe_load(Path(path).read_text())
    return InputConfig(**data)


def compute_drone_context(cfg: InputConfig) -> List[Dict]:
    drones = []
    start, end = cfg.drone.start_ip, cfg.drone.end_ip
    base_pose = [float(p) for p in cfg.gazebo.px4_gz_model_pose.split(",")]

    for i in range(start, end + 1):
        offset = i - start
        x = base_pose[0] + offset * 2
        y = base_pose[1] + offset * 2
        z, roll, pitch, yaw = base_pose[2:]
        drone_ip = f"{cfg.network.base_ip}{cfg.network.swarm_subnet}.{i}"
        envoy_ip = f"{cfg.network.base_ip}{cfg.network.swarm_subnet}.{i + 100}"
        px4_pose = f"{x:.2f},{y:.2f},{z},{roll},{pitch},{yaw}"
        gz_ip = f"{cfg.network.base_ip}{cfg.network.swarm_subnet}.1"
        if cfg.gazebo.gz_sim:
            px4_command = (
                f"sleep 3 && "
                f"GZ_PARTITION={cfg.gazebo.gz_partition_name} "
                f"GZ_RELAY= {gz_ip}"  # {cfg.gazebo.gz_ip} "
                f"GZ_IP={drone_ip} "
                f'PX4_GZ_MODEL_POSE="{px4_pose}" '
                f"PX4_GZ_STANDALONE=1 "
                f"PX4_SYS_AUTOSTART=4001 "
                f"PX4_SIM_MODEL={cfg.drone.drone_model} "
                f"/root/PX4-Autopilot/build/px4_sitl_default/bin/px4 -i {i - start}"
            )
        else:
            px4_command = (
                f"sleep 3 && "
                f"HEADLESS=1 "
                f"PX4_SYS_AUTOSTART=4001 "
                f"PX4_SIM_MODEL={cfg.drone.drone_model} "
                f"/root/PX4-Autopilot/build/px4_sitl_default/bin/px4 -i {i - start}"
            )
        drones.append(
            {
                "i": i,
                "drone_name": f"drone_{i}",
                "image": cfg.drone.image,
                "drone_ip": drone_ip,
                "envoy_ip": envoy_ip,
                "px4_pose": px4_pose,
                "gz_sim": cfg.gazebo.gz_sim,
                "gz_partition_name": cfg.gazebo.gz_partition_name,
                "gz_ip": str(cfg.gazebo.gz_ip),
                "drone_model": cfg.drone.drone_model,
                "network_name": cfg.network.target_base_name,
                "base_ip": cfg.network.base_ip,
                "opa_policy": cfg.drone.opa_policy,
                "px4_command": px4_command,
            }
        )
    return drones


def main():
    # Run the shell script
    result = subprocess.run(
        ["bash", "../scripts/network_setup.sh"],
        check=True,
        capture_output=True,
        text=True,
    )

    # Parse the export statements
    for line in result.stdout.splitlines():
        if line.startswith("export "):
            # Remove 'export ' and split at '='
            key, val = line[len("export ") :].split("=", 1)
            # Strip quotes
            val = val.strip("'\"")
            os.environ[key] = val

    # # Now SELECTED_NETWORK_NAME and SELECTED_SUBNET are available
    # network_name = os.environ["SELECTED_NETWORK_NAME"]
    # # Construct with shell-derived values
    # network_cfg = NetworkConfig(
    #     target_base_name=network_name, swarm_subnet=int(swarm_subnet)
    # )

    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="Path to input_config.yml")

    args = parser.parse_args()

    cfg = load_config(args.config)

    # override network info if environment variables are set
    cfg.network.target_base_name = os.getenv(
        "SELECTED_NETWORK_NAME", cfg.network.target_base_name
    )
    cfg.network.swarm_subnet = int(
        os.environ.get(
            "SELECTED_SUBNET", f"{cfg.network.base_ip}{cfg.network.swarm_subnet}.0/24"
        ).split(".")[2]
    )

    env = Environment(loader=FileSystemLoader("templates"), undefined=StrictUndefined)
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "tmuxinator_config").mkdir(exist_ok=True)
    (out_dir / "envoy_config").mkdir(exist_ok=True)
    (out_dir / "dockercompose_config").mkdir(exist_ok=True)

    for drone in compute_drone_context(cfg):
        (
            out_dir / f"dockercompose_config/docker-compose-{drone['drone_name']}.yml"
        ).write_text(env.get_template("docker-compose-per-drone.j2").render(**drone))
        (out_dir / f"tmuxinator_config/{drone['drone_name']}.yml").write_text(
            env.get_template("tmuxinator.j2").render(**drone)
        )
        (out_dir / f"envoy_config/{drone['drone_name']}.yml").write_text(
            env.get_template("envoy.j2").render(**drone)
        )


if __name__ == "__main__":
    main()

#
# def load_config(path: str) -> InputConfig:
#     data = yaml.safe_load(Path(path).read_text())
#     cfg = InputConfig(**data)  # Pydantic validates everything here
#     return cfg
#
#
# def compute_drone_context(cfg: InputConfig) -> List[Dict]:
#     drones = []
#     start, end = cfg.drone.start_ip, cfg.drone.end_ip
#
#     base_pose = [float(p) for p in cfg.gazebo.px4_gz_model_pose.split(",")]
#
#     for i in range(start, end + 1):
#         offset = i - start
#         x = base_pose[0] + offset * 2
#         y = base_pose[1] + offset * 2
#         z, roll, pitch, yaw = base_pose[2:]
#
#         drone_ip = f"{cfg.network.base_ip}{cfg.network.swarm_subnet}.{i}"
#         px4_pose = f"{x:.2f},{y:.2f},{z},{roll},{pitch},{yaw}"
#
#         drones.append(
#             {
#                 "i": i,
#                 "drone_name": f"drone_{i}",
#                 "drone_ip": drone_ip,
#                 "px4_pose": px4_pose,
#                 "gz_sim": cfg.gazebo.gz_sim,
#                 "gz_partition_name": cfg.gazebo.gz_partition_name,
#                 "gz_ip": str(cfg.gazebo.gz_ip),
#                 "drone_model": cfg.drone.drone_model,
#                 "network_name": cfg.network.target_base_name,
#                 "base_ip": cfg.network.base_ip,
#                 "opa_policy": cfg.drone.opa_policy,
#             }
#         )
#     return drones
#
#
# env = Environment(
#     loader=FileSystemLoader("templates"),
#     undefined=StrictUndefined,
#     keep_trailing_newline=True,
# )
# env.filters["yaml_quote"] = lambda s: f'"{s}"' if "," in s else s
#
# for drone in compute_drone_context(cfg):
#     compose = env.get_template("docker-compose-per-drone.j2").render(**drone)
#     tmux = env.get_template("tmuxinator.j2").render(**drone)
#     envoy = env.get_template("envoy.j2").render(**drone)
#
#     out_dir = Path("outputs")
#     out_dir.mkdir(exist_ok=True)
#     (out_dir / "tmuxinator_config").mkdir(exist_ok=True)
#     (out_dir / "envoy_config").mkdir(exist_ok=True)
#
#     (out_dir / f"docker-compose-{drone['drone_name']}.yml").write_text(compose)
#     (out_dir / f"tmuxinator_config/{drone['drone_name']}.yml").write_text(tmux)
#     (out_dir / f"envoy_config/{drone['drone_name']}.yaml").write_text(envoy)
#
# #
# # def yaml_quote(s):
# #     s = "" if s is None else str(s)
# #     # If contains characters that need quoting in YAML, double-quote and escape
# #     if any(ch in s for ch in [":", "-", ",", "\n", '"', "'"]):
# #         return '"' + s.replace('"', '\\"') + '"'
# #     return s
# #
# #
# # def atomic_write(path: Path, data: str):
# #     tmp = path.with_suffix(path.suffix + ".tmp")
# #     tmp.write_text(data)
# #     if path.exists() and path.read_text() == data:
# #         tmp.unlink()
# #         return False
# #     tmp.replace(path)
# #     return True
# #
# #
# # def main():
# #     p = argparse.ArgumentParser()
# #     p.add_argument("config", help="input_config.yml")
# #     p.add_argument("--out", default="outputs", help="output dir")
# #     args = p.parse_args()
# #
# #     cfg = yaml.safe_load(open(args.config))
# #     gz = cfg.get("gazebo", {})
# #     dr = cfg.get("drone", {})
# #     nw = cfg.get("network", {})
# #
# #     start = int(dr.get("start_ip", 101))
# #     end = int(dr.get("end_ip", 104))
# #
# #     env = Environment(
# #         loader=FileSystemLoader("templates"),
# #         undefined=StrictUndefined,
# #         keep_trailing_newline=True,
# #     )
# #     env.filters["yaml_quote"] = yaml_quote
# #
# #     out_dir = Path(args.out)
# #     out_dir.mkdir(parents=True, exist_ok=True)
# #     (out_dir / "tmuxinator_config").mkdir(exist_ok=True)
# #     (out_dir / "envoy_config").mkdir(exist_ok=True)
# #
# #     for i in range(start, end + 1):
# #         offset = i - start
# #         # compute pose like your bash: base + offset*2
# #         base_pose = (
# #             dr.get("px4_gz_model_pose")
# #             or gz.get("px4_gz_model_pose")
# #             or "268.08,-128.22,3.86,0.00,0,-0.7"
# #         )
# #         parts = [p.strip() for p in base_pose.split(",")]
# #         try:
# #             bx, by = float(parts[0]), float(parts[1])
# #         except Exception:
# #             bx, by = 268.08, -128.22
# #         x = bx + offset * 2
# #         y = by + offset * 2
# #         z, roll, pitch, yaw = (
# #             parts[2:] if len(parts) >= 6 else ["3.86", "0.00", "0", "-0.7"]
# #         )
# #         px4_pose = f"{x:.2f},{y:.2f},{z},{roll},{pitch},{yaw}"
# #
# #         ctx = {
# #             "i": i,
# #             "drone_name": f"drone_{i}",
# #             "network_name": nw.get("target_base_name", "swarm_net"),
# #             "base_ip": nw.get("base_ip", "192.168."),
# #             "swarm_subnet": nw.get("swarm_subnet", "132"),
# #             "drone_ip": f"{nw.get('base_ip', '192.168.')}{nw.get('swarm_subnet', '132')}.{i}",
# #             "envoy_file": f"./envoy_config/drone_{i}.yaml",
# #             "opa_policy": dr.get("opa_policy", "./opa/policy.rego"),
# #             "container": dr.get("image", "client_drone_ros2_px4"),
# #             "gz_partition_name": gz.get("gz_partition_name", "relay"),
# #             "gz_ip": gz.get("gz_ip", "192.168.132.1"),
# #             "px4_pose": px4_pose,
# #             "px4_command": "",  # will be set below depending on gz_sim
# #         }
# #
# #         gz_sim = str(gz.get("gz_sim", "false")).lower()
# #         if gz_sim in ("1", "true", "yes"):
# #             ctx["px4_command"] = (
# #                 f"GZ_PARTITION={ctx['gz_partition_name']} GZ_RELAY={ctx['gz_ip']} "
# #                 f'GZ_IP={ctx["drone_ip"]} PX4_GZ_MODEL_POSE="{px4_pose}" PX4_GZ_STANDALONE=1 '
# #                 f"PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL={dr.get('drone_model', 'gz_x500')} "
# #                 "/root/PX4-Autopilot/build/px4_sitl_default/bin/px4 -i 0"
# #             )
# #         else:
# #             ctx["px4_command"] = (
# #                 f"HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL={dr.get('drone_model', 'gz_x500')} /root/PX4-Autopilot/build/px4_sitl_default/bin/px4 -i 0"
# #             )
# #
# #         # render files
# #         compose = env.get_template("docker-compose-per-drone.j2").render(**ctx)
# #         tmux = env.get_template("tmuxinator.j2").render(**ctx)
# #         envoy = env.get_template("envoy.j2").render(**ctx)
# #
# #         changed = atomic_write(
# #             out_dir / f"docker-compose-{ctx['drone_name']}.yml", compose
# #         )
# #         atomic_write(out_dir / f"tmuxinator_config/{ctx['drone_name']}.yml", tmux)
# #         atomic_write(out_dir / f"envoy_config/{ctx['drone_name']}.yaml", envoy)
# #         print(f"Rendered {ctx['drone_name']} (changed={changed})")
# #
# #
# # if __name__ == "__main__":
# #     main()
