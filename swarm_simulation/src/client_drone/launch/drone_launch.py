# from launch import LaunchDescription
# from launch.actions import ExecuteProcess
# from launch_ros.actions import Node
#
#
# def generate_launch_description():
#     return LaunchDescription(
#         [
#             ExecuteProcess(
#                 cmd=["MicroXRCEAgent", "udp4", "-p", "8888"],
#                 name="micro_xrce_dds_agent",
#                 output="screen",
#             ),
#             Node(
#                 package="client_drone",
#                 executable="client",
#                 name="clientt",
#                 output="screen",
#             ),
#             Node(
#                 package="client_drone",
#                 executable="drone_data_sender",
#                 name="drone_data_sender",
#                 output="screen",
#             ),
#         ]
#     )
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_share = get_package_share_directory("client_drone")
    default_yaml = os.path.join(pkg_share, "config", "client_config.yaml")

    yaml_arg = DeclareLaunchArgument("yaml_file", default_value=default_yaml)
    drone_id_arg = DeclareLaunchArgument("drone_id", default_value="droneX")
    group_id_arg = DeclareLaunchArgument("group_id", default_value="groupX")
    etcd_host_arg = DeclareLaunchArgument("etcd_host", default_value="127.0.0.1:2379")

    client = Node(
        package="client_drone",
        executable="client",
        name="client_node",
        output="screen",
        parameters=[
            {
                "yaml_file": LaunchConfiguration("yaml_file"),
                "drone_id": LaunchConfiguration("drone_id"),
                "group_id": LaunchConfiguration("group_id"),
                "etcd_host": LaunchConfiguration("etcd_host"),
            }
        ],
    )

    ftp_opa = Node(
        package="client_drone",
        executable="receive_ftp_write_opa",
        name="mavlink_ftp_receiver",
        output="screen",
    )

    return LaunchDescription(
        [yaml_arg, drone_id_arg, group_id_arg, etcd_host_arg, client, ftp_opa]
    )
