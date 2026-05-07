from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, IncludeLaunchDescription, GroupAction
from launch_ros.actions import Node, SetRemap, SetParameter
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command, PathJoinSubstitution
import os


'''
Simulation setup for spawning the bot in a Gazebo world, and run the bot
aroud using keyboard commands, and create a map using SLAM Toolbox.
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

        # SLAM Toolbox for mapping (Forced Remap & Forced Sim Time)
        GroupAction(
            actions=[
                SetParameter(name='use_sim_time', value=True), # <--- ADD THIS
                SetRemap(src='/scan', dst='/lidar'),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        PathJoinSubstitution([FindPackageShare('slam_toolbox'), 'launch', 'online_async_launch.py'])
                    ]),
                    launch_arguments={
                        'slam_params_file': PathJoinSubstitution([FindPackageShare('robo_gazebo'), 'config', 'mapper_params.yaml']),
                        'use_sim_time': 'true'
                    }.items()
                )
            ]
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