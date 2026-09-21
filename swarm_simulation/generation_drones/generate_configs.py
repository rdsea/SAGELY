#!/usr/bin/env python3

from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from pydantic import BaseModel, IPvAnyAddress, field_validator, ValidationInfo

from typing import Dict, List, Optional

import argparse

import subprocess
import os


class GazeboConfig(BaseModel):
    gz_sim: bool = False
    gz_partition_name: str = "relay"
    gz_ip: Optional[IPvAnyAddress] = None
    world_model: str
    px4_gz_model_pose: str = "268.08,-128.22,3.86,0.00,0,-0.7"

    @field_validator("px4_gz_model_pose")
    @classmethod
    def validate_pose(cls, v: str) -> str:
        parts = v.split(",")
        if len(parts) != 6:
            raise ValueError("px4_gz_model_pose must have 6 comma-separated floats")
        return v

    # @field_validator("px4_gz_model_pose")
    # def validate_pose(cls, v):
    #     parts = v.split(",")
    #     if len(parts) != 6:
    #         raise ValueError("px4_gz_model_pose must have 6 comma-separated floats")
    #     return v


class DroneConfig(BaseModel):
    image: str
    start_ip: int
    end_ip: int
    drone_model: str = "gz_x500"
    opa_policy: str = "policy.rego"

    @field_validator("end_ip")
    @classmethod
    def end_after_start(cls, v: int, info: ValidationInfo) -> int:
        start_ip = info.data.get("start_ip")
        if start_ip is not None and v < start_ip:
            raise ValueError("end_ip must be >= start_ip")
        return v

    # @field_validator("end_ip")
    # def end_after_start(cls, v, values):
    #     if "start_ip" in values and v < values["start_ip"]:
    #         raise ValueError("end_ip must be >= start_ip")
    #     return v


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
    script_dir = Path(__file__).resolve().parent
    network_setup = (
        script_dir.parent / "generation_drones" / "scripts" / "network_setup.sh"
    )
    result = subprocess.run(
        ["bash", str(network_setup)],
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

    env = Environment(
        loader=FileSystemLoader(script_dir / "templates"), undefined=StrictUndefined
    )
    out_dir = script_dir / "outputs"
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
