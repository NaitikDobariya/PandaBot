import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction, IncludeLaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import Command, PathJoinSubstitution

def generate_launch_description():
    pkg_desc = get_package_share_directory('robo_description')
    pkg_gazebo = get_package_share_directory('robo_gazebo')
    pkg_nav = get_package_share_directory('robo_navigation')
    
    # Paths
    robot_desc_path = os.path.join(pkg_desc, 'urdf', 'robot.urdf.xacro')
    bridge_config = os.path.join(pkg_gazebo, 'config', 'gz_bridge.yaml')
    map_path = os.path.join(pkg_gazebo, 'worlds', 'sim_world.sdf')
    
    # Nav2 Paths
    nav_map_file = os.path.join(pkg_nav, 'maps', 'map.yaml')
    nav_params_file = os.path.join(pkg_nav, 'config', 'nav2_params.yaml')
    # twist_mux_params = os.path.join(pkg_gazebo, 'config', 'twist_mux.yaml')

    return LaunchDescription([
        # 1. Start Gazebo & Bridges
        ExecuteProcess(cmd=['ign', 'gazebo', '-r', map_path, '-v', '4'], output='screen'),
        
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command(['xacro ', robot_desc_path]), 'use_sim_time': True}]
        ),
        
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'use_sim_time': True}],
            arguments=['--ros-args', '-p', f'config_file:={bridge_config}']
        ),

        # Spawn Robot (Delayed 3s)
        TimerAction(
            period=3.0,
            actions=[ExecuteProcess(cmd=['ros2', 'run', 'ros_gz_sim', 'create', '-topic', 'robot_description', '-name', 'my_robot', '-z', '0.2'])]
        ),
        
        # 4. Nav2 Bringup (Delayed 8s)
        TimerAction(
            period=8.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py'])]),
                    launch_arguments={
                        'map': nav_map_file,
                        'params_file': nav_params_file,
                        'use_sim_time': 'true'
                    }.items()
                )
            ]
        ),
    ])