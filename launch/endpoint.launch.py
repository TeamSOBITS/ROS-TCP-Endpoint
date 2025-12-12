from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    declare_ros_ip_cmd = DeclareLaunchArgument(
        'ros_ip',
        default_value='0.0.0.0',
        description='ROS IP address for ros_tcp_endpoint'
    )
    ros_ip = LaunchConfiguration('ros_ip')
    endpoint_node = Node(
        package='ros_tcp_endpoint',
        executable='default_server_endpoint',
        name='ros_tcp_endpoint',
        output='screen',
        parameters=[{'ROS_IP': ros_ip}]
    )
    return LaunchDescription(
        [
            declare_ros_ip_cmd,
            endpoint_node,
        ]
    )
