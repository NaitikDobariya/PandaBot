#!/usr/bin/env python3

import os
import sys
import struct
import threading
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class JoyTeleop(Node):

    def __init__(self):
        super().__init__('joy_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # --------------------------------------------------------
        # CONFIGURATION (Adjust these to tweak the feel!)
        # --------------------------------------------------------
        # Max safety limits
        self.max_linear = 0.5    # m/s
        self.max_angular = 0.8   # rad/s

        # Acceleration step sizes per loop cycle (Fires at 50Hz / every 20ms)
        # Higher = snappy/jerky | Lower = smooth/gradual acceleration
        self.step_linear = 0.01   # Takes ~0.6 seconds to reach full speed
        self.step_angular = 0.05  # Takes ~0.3 seconds to reach full spin

        # Joystick Mappings (Based on your raw telemetry output)
        self.AXIS_LINEAR = 1      # Left Knob (Up/Down)
        self.AXIS_ANGULAR = 0     # Right Knob (Left/Right)
        self.DEADZONE = 0.05      # Ignore micro-jitters when stick is untouched
        self.js_device = '/dev/input/js0'
        # --------------------------------------------------------

        # Speed tracking variables
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.current_linear = 0.0
        self.current_angular = 0.0

        # Verify hardware port exists
        if not os.path.exists(self.js_device):
            self.get_logger().error(f"Device {self.js_device} not found! Is it plugged into the container?")
            sys.exit(1)

        # Spawn background thread to read the raw binary file stream
        self.running = True
        self.reader_thread = threading.Thread(target=self.read_joystick_stream, daemon=True)
        self.reader_thread.start()

        # Timed loop running at 50Hz (every 0.02s) to compute acceleration & publish
        self.timer = self.create_timer(0.02, self.physics_and_publisher_loop)

        print("\n======================================================")
        print(" RAW HIGH-PERFORMANCE TELEOP NODE ACTIVE")
        print(f" Reading hardware directly from: {self.js_device}")
        print(" Smooth Acceleration & Deadzones: ENABLED")
        print(" Press CTRL+C to safely exit.")
        print("======================================================\n")

    def read_joystick_stream(self):
        """ Runs in a background thread to intercept raw USB events """
        try:
            with open(self.js_device, 'rb') as f:
                while self.running:
                    evbuf = f.read(8)
                    if not evbuf:
                        break
                    
                    # Unpack standard Linux joystick 8-byte structure
                    _, value, type_, number = struct.unpack('IhBB', evbuf)
                    type_ &= ~0x80 # Strip initial state flag

                    # We only care about Axis movements (Type 2)
                    if type_ == 2:
                        norm_value = value / 32367.0 # Normalize to -1.0 to 1.0

                        # Apply deadzone to treat near-zero positions as absolute neutral
                        if abs(norm_value) < self.DEADZONE:
                            norm_value = 0.0

                        # Update Linear Target (Left stick)
                        # NOTE: Linux sticks report negative when pushed UP, so we invert it (-)
                        if number == self.AXIS_LINEAR:
                            self.target_linear = -norm_value * self.max_linear

                        # Update Angular Target (Right stick)
                        # NOTE: ROS expects positive values to turn LEFT, so we invert this too (-)
                        elif number == self.AXIS_ANGULAR:
                            self.target_angular = -norm_value * self.max_angular

        except Exception as e:
            self.get_logger().error(f"Error reading joystick stream: {e}")

    def physics_and_publisher_loop(self):
        """ Runs at a fixed 50Hz to handle smooth acceleration ramps """
        twist = Twist()

        # --- Linear Acceleration Physics ---
        diff_linear = self.target_linear - self.current_linear
        if abs(diff_linear) <= self.step_linear:
            self.current_linear = self.target_linear  # Close enough, snap to target
        else:
            self.current_linear += math.copysign(self.step_linear, diff_linear)

        # --- Angular Acceleration Physics ---
        diff_angular = self.target_angular - self.current_angular
        if abs(diff_angular) <= self.step_angular:
            self.current_angular = self.target_angular
        else:
            self.current_angular += math.copysign(self.step_angular, diff_angular)

        # Assign values to ROS message
        twist.linear.x = self.current_linear
        twist.angular.z = self.current_angular
        self.pub.publish(twist)

        # Live clean terminal telemetry feed
        print(f"\rTarget: [L: {self.target_linear: >5.2f} | A: {self.target_angular: >5.2f}] --> Actual: [L: {self.current_linear: >5.2f} | A: {self.current_angular: >5.2f}]    ", end="", flush=True)

    def destroy_node(self):
        self.running = False
        # Publish an absolute zero stop command before vanishing
        stop_twist = Twist()
        self.pub.publish(stop_twist)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = JoyTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n\nEmergency Stopping Robot and shutting down node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()