import launch
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            ExecuteProcess(
                cmd=["MicroXRCEAgent", "udp4", "-p", "8888"],
                name="micro_xrce_dds_agent",
                output="screen",
            ),
            Node(
                package="client_drone",
                executable="client",
                name="clientt",
                output="screen",
            ),
            Node(
                package="client_drone",
                executable="drone_data_sender",
                name="drone_data_sender",
                output="screen",
            ),
        ]
    )
