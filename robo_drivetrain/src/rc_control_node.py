#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial

class DrivetrainBridge(Node):
    def __init__(self):
        super().__init__('drivetrain_bridge')
        
        # --- Serial Connection ---
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 115200
        
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=0.05)
            self.get_logger().info(f"Connected to Arduino on {self.serial_port} - Ready for /cmd_vel")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Serial: {e}")
            raise SystemExit

        # --- Subscriptions ---
        self.sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        # --- Conversion Tuning ---
        # These match the max limits in your keyboard teleop node
        self.max_linear = 0.3  # m/s
        self.max_angular = 0.8 # rad/s
        self.max_pwm = 255

    def cmd_vel_callback(self, msg):
        # 1. Scale ROS velocities to raw PWM (-255 to 255)
        pwm_forward = -(msg.linear.x / self.max_linear) * self.max_pwm
        pwm_steer = -(msg.angular.z / self.max_angular) * self.max_pwm

        # 2. Arcade Drive Mixing (Forward + Steering)
        left_pwm = int(pwm_forward - pwm_steer)
        right_pwm = int(pwm_forward + pwm_steer)

        # 3. Safety Clamp (Ensure we never send illegal values to the Cytron driver)
        left_pwm = max(-self.max_pwm, min(self.max_pwm, left_pwm))
        right_pwm = max(-self.max_pwm, min(self.max_pwm, right_pwm))

        # 4. Blast it to the Arduino ("P,left,right\n")
        command = f"P,{left_pwm},{right_pwm}\n"
        self.ser.write(command.encode())

def main():
    rclpy.init()
    node = DrivetrainBridge()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Emergency hard-stop sent to Arduino when you kill this node
        try:
            node.ser.write(b"P,0,0\n")
            node.ser.close()
        except:
            pass
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()