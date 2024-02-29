import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    roboclaw_params = os.path.join(
        get_package_share_directory('osr_bringup'),
        'config',
        'roboclaw_params.yaml'
    )
    osr_params = os.path.join(
        get_package_share_directory('osr_bringup'),
        'config',
        'osr_params.yaml'
    )

    ld = LaunchDescription()
    
    ld.add_action(
        Node(
            package='osr_control',
            executable='roboclaw_wrapper',
            name='roboclaw_wrapper',
            output='screen',
            emulate_tty=True,
            parameters=[roboclaw_params]
        )
    )
    ld.add_action(
        DeclareLaunchArgument('enable_odometry', default_value='false')
    )
    ld.add_action(
        DeclareLaunchArgument('enable_odometry', default_value='false')
    )

    return ld
