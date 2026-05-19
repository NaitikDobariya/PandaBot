#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import serial
import math
import time

class DrivetrainDriver(Node):
    def __init__(self):
        super().__init__('drivetrain_driver')
        
        # --- Robot Physical Parameters (TUNE THESE!) ---
        self.wheel_radius = 0.033  # Meters (e.g., 66mm diameter wheel)
        self.wheel_base = 0.16     # Meters (distance between left and right wheel centers)
        self.ticks_per_rev = 330.0 # Encoder ticks for one full wheel rotation
        self.max_speed_ms = 0.5    # Maximum physical speed in m/s (maps to 255 PWM)

        # --- State Variables ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last_ticks_l = 0
        self.last_ticks_r = 0
        self.last_time = self.get_clock().now()
        self.first_read = True

        # --- Serial Connection ---
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            self.get_logger().info("Connected to Arduino via Serial.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            return

        # --- ROS 2 Interfaces ---
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 10)
        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Timer to read Serial and publish Odometry at 20Hz (0.05s)
        self.timer = self.create_timer(0.05, self.read_serial_and_publish_odom)

    def cmd_vel_callback(self, msg):
        # 1. Extract velocities from ROS Twist message
        v = msg.linear.x
        w = msg.angular.z

        # 2. Convert to Left and Right wheel target speeds (m/s)
        v_l = v - (w * self.wheel_base / 2.0)
        v_r = v + (w * self.wheel_base / 2.0)

        # 3. Map physical speeds to PWM limits (-255 to 255)
        pwm_l = int((v_l / self.max_speed_ms) * 255)
        pwm_r = int((v_r / self.max_speed_ms) * 255)

        # Cap the PWM to prevent overflowing Arduino ints
        pwm_l = max(min(pwm_l, 255), -255)
        pwm_r = max(min(pwm_r, 255), -255)

        # 4. Send to Arduino
        command = f"{pwm_l},{pwm_r}\n"
        self.serial_port.write(command.encode('utf-8'))

    def read_serial_and_publish_odom(self):
        if not self.serial_port.in_waiting:
            return

        # 1. Read Serial String from Arduino
        line = self.serial_port.readline().decode('utf-8').strip()
        try:
            ticks_str = line.split(',')
            current_ticks_l = int(ticks_str[0])
            current_ticks_r = int(ticks_str[1])
        except (ValueError, IndexError):
            return # Ignore garbage data during startup

        if self.first_read:
            self.last_ticks_l = current_ticks_l
            self.last_ticks_r = current_ticks_r
            self.first_read = False
            return

        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9

        # 2. Calculate Distance Traveled by each wheel
        delta_ticks_l = current_ticks_l - self.last_ticks_l
        delta_ticks_r = current_ticks_r - self.last_ticks_r

        dist_l = (delta_ticks_l / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)
        dist_r = (delta_ticks_r / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)

        # 3. Calculate Robot displacement
        delta_distance = (dist_l + dist_r) / 2.0
        delta_theta = (dist_r - dist_l) / self.wheel_base

        # 4. Update Global Pose (X, Y, Theta)
        self.x += delta_distance * math.cos(self.th + (delta_theta / 2.0))
        self.y += delta_distance * math.sin(self.th + (delta_theta / 2.0))
        self.th += delta_theta

        # 5. Calculate instantaneous velocities
        v_current = delta_distance / dt
        w_current = delta_theta / dt

        # Update historical trackers
        self.last_ticks_l = current_ticks_l
        self.last_ticks_r = current_ticks_r
        self.last_time = current_time

        # 6. Publish Odometry Message and TF
        self.publish_odom(current_time.to_msg(), v_current, w_current)

    def publish_odom(self, stamp, v, w):
        # Convert yaw (Theta) to Quaternion
        q_z = math.sin(self.th / 2.0)
        q_w = math.cos(self.th / 2.0)

        # --- Transform Broadcaster (odom -> base_link) ---
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = q_z
        t.transform.rotation.w = q_w
        self.tf_broadcaster.sendTransform(t)

        # --- Odometry Message ---
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = q_z
        odom.pose.pose.orientation.w = q_w
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w
        self.odom_publisher.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = DrivetrainDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()