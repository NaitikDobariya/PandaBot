# This launch file gets all the sub-systems of the robot going and starts publishing the data.
# It acts as the primary hardware interface layer before the Nav2 stack is launched.

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    
    # Paths to packages 
    bringup_share = FindPackageShare('robo_bringup')
    description_share = FindPackageShare('robo_description')
    
    # Assuming you saved your new robot xacro inside the description package's urdf folder
    xacro_file = PathJoinSubstitution([description_share, 'urdf', 'robot.urdf.xacro'])

    return LaunchDescription([

        # robot_state_publisher 
        # Processes the XACRO and broadcasts the entire TF tree seamlessly, the xacro file reades the VibeChecker URDF automatically
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['xacro ', xacro_file])
            }],
            output='screen'
        ),

        # Launch the IMU Driver 
        # A very important thing we did here is that we did not launch the IMU_launch.launch.py, because that had another robot_state_publisher
        # inside it, which might result in two nodes publishing the same TF, which is not stable.
        Node(
            package='IMU_driver',
            executable='driver_node.py',
            name='imu_driver_node',
            output='screen'
        ),

        # Launch the RPLidar A1M8
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',  
                'serial_baudrate': 115200,      # <-- A1M8 specific baudrate
                'frame_id': 'lidar_link',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }],
            output='screen'
        ),

        # Drivetrain driver node
        # Inverse/Forward Kinematics, and publishes the /odom topic.
        Node(
            package='robo_drivetrain',
            executable='drivetrain_node.py',
            name='drivetrain_bridge',
            parameters=[{
                'serial_port': '/dev/ttyACM0',  # <-- Arduino port, need to change this later.
                'wheel_radius': 0.110,
                'wheel_base': 0.30,
                'ticks_per_rev': 495.0
            }],
            output='screen'
        ),

    ])