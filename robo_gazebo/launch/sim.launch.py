from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command
import os

'''
Simple simulation setup for spawning the bot in a Gazebo world, and run the bot
around using keyboard commands.
'''


def generate_launch_description():

    pkg_desc = get_package_share_directory('robo_description')
    pkg_gazebo = get_package_share_directory('robo_gazebo')

    robot_desc_path = os.path.join(pkg_desc, 'urdf', 'robot.urdf.xacro')
    bridge_config = os.path.join(pkg_gazebo, 'config', 'gz_bridge.yaml')

    map_path = os.path.join(pkg_gazebo, 'worlds', 'sim_world.sdf')

    return LaunchDescription([

        # Start Gazebo (gz)
        ExecuteProcess(
            cmd=['ign', 'gazebo', '-r', map_path, '-v', '4'],
            output='screen'
        ),

        # Publish robot description
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['xacro ', robot_desc_path]),
                'use_sim_time': True
            }],
            output='screen'
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=[
                '--ros-args',
                '-p',
                f'config_file:={bridge_config}'
            ],
            output='screen'
        ),

        # Spawn robot into gz, with some delay
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        'ros2', 'run', 'ros_gz_sim', 'create',
                        '-topic', 'robot_description',
                        '-name', 'my_robot',
                        '-z', '0.2'
                    ],
                    output='screen'
                )
            ]
        ),
    ])