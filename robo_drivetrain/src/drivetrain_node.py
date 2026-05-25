#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import serial
import math
import time

class DrivetrainBridge(Node):
    def __init__(self):
        super().__init__('drivetrain_bridge')
        
        # --- 1. Robot Parameters ---
        self.declare_parameter('wheel_radius', 0.110)
        self.declare_parameter('wheel_base', 0.30)
        self.declare_parameter('ticks_per_rev', 495.0)
        
        self.R = self.get_parameter('wheel_radius').value
        self.L = self.get_parameter('wheel_base').value
        self.TPR = self.get_parameter('ticks_per_rev').value
        self.loop_rate = 20.0 # Hz

        # --- 2. State Variables (For Forward Kinematics) ---
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last_ticks_l = 0
        self.last_ticks_r = 0
        self.last_time = self.get_clock().now()
        self.first_run = True

        # --- 3. Serial Setup ---
        self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.05)

        # --- 4. ROS Interfaces ---
        self.sub = self.create_subscription(Twist, 'cmd_vel', self.inverse_kinematics_cb, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_br = TransformBroadcaster(self)
        self.timer = self.create_timer(1.0/self.loop_rate, self.forward_kinematics_loop)

    def inverse_kinematics_cb(self, msg):
        """ Translates Robot Velocity -> Wheel Ticks/Loop """
        v = msg.linear.x
        w = msg.angular.z

        # IK Math
        v_l = v - (w * self.L / 2.0)
        v_r = v + (w * self.L / 2.0)

        # Convert m/s to Ticks per Loop for the Arduino PID
        # (v / circumference) * ticks_per_rev / frequency
        circ = 2 * math.pi * self.R
        target_l = (v_l / circ) * self.TPR / self.loop_rate
        target_r = (v_r / circ) * self.TPR / self.loop_rate

        # Send to Arduino
        self.ser.write(f"{target_l:.2f},{target_r:.2f}\n".encode())

    def forward_kinematics_loop(self):
        """ Translates Encoder Ticks -> Robot Pose (Odometry) """
        if not self.ser.in_waiting:
            return

        try:
            line = self.ser.readline().decode().strip()
            curr_l, curr_r = map(int, line.split(','))
        except:
            return

        now = self.get_clock().now()
        if self.first_run:
            self.last_ticks_l, self.last_ticks_r = curr_l, curr_r
            self.last_time = now
            self.first_run = False
            return

        dt = (now - self.last_time).nanoseconds / 1e9
        
        # Calculate distance traveled by wheels since last loop
        d_l = ((curr_l - self.last_ticks_l) / self.TPR) * (2 * math.pi * self.R)
        d_r = ((curr_r - self.last_ticks_r) / self.TPR) * (2 * math.pi * self.R)

        # FK Math: Displacement and Rotation
        d_center = (d_l + d_r) / 2.0
        phi = (d_r - d_l) / self.L

        # Update Global Pose
        self.x += d_center * math.cos(self.th + phi/2.0)
        self.y += d_center * math.sin(self.th + phi/2.0)
        self.th += phi

        # Velocities for the Odom message
        v_final = d_center / dt
        w_final = phi / dt

        self.publish_odom(now, v_final, w_final)

        # Update history
        self.last_ticks_l, self.last_ticks_r = curr_l, curr_r
        self.last_time = now

    def publish_odom(self, now, v, w):
        # Convert Theta to Quaternion
        qz = math.sin(self.th / 2.0)
        qw = math.cos(self.th / 2.0)

        # 1. Publish TF (odom -> base_link)
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_br.sendTransform(t)

        # 2. Publish Odometry Message
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w
        self.odom_pub.publish(odom)

def main():
    rclpy.init()
    node = DrivetrainBridge()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()