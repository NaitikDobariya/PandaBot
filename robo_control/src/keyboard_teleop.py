#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty

msg = """
Control Your Robot (Incremental Throttle)
---------------------------
w : accelerate forward (+0.05)
x : accelerate backward (-0.05)
a : steer left (+0.1)
d : steer right (-0.1)
s/space : emergency stop (0.0)

Tap keys for micro-adjustments.
Hold keys to continuously increase speed.
CTRL-C to quit
"""

class KeyboardTeleop(Node):

    def __init__(self):
        super().__init__('keyboard_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Max safety limits
        self.max_linear = 0.3
        self.max_angular = 0.8

        # Step sizes (How much speed to add per keypress/loop)
        self.step_linear = 0.05
        self.step_angular = 0.1

        # Current actual speeds
        self.current_linear = 0.0
        self.current_angular = 0.0

        print(msg)

    def get_key(self):
        # 10Hz read rate
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
            if key == '\x1b': 
                sys.stdin.read(2) # Clears out arrow key escape characters
                return ''
            return key
        return ''

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()

                # Directly increment/decrement the speed limits, capped by min/max
                if key == 'w':
                    self.current_linear = min(self.max_linear, self.current_linear + self.step_linear)
                elif key == 'x':
                    self.current_linear = max(-self.max_linear, self.current_linear - self.step_linear)
                elif key == 'a':
                    self.current_angular = min(self.max_angular, self.current_angular + self.step_angular)
                elif key == 'd':
                    self.current_angular = max(-self.max_angular, self.current_angular - self.step_angular)
                elif key in ['s', ' ']:
                    self.current_linear = 0.0
                    self.current_angular = 0.0
                elif key == '\x03':
                    break

                # The script keeps looping and publishing this twist message at 10Hz
                # even if no key is currently being pressed (maintains current speed)
                twist = Twist()
                twist.linear.x = self.current_linear
                twist.angular.z = self.current_angular
                self.pub.publish(twist)

                # Live terminal feedback
                print(f"\rCurrent Linear: {self.current_linear: >5.2f} | Current Angular: {self.current_angular: >5.2f}    ", end="", flush=True)

        except Exception as e:
            print(f"\nError in teleop loop: {e}")

        finally:
            self.pub.publish(Twist()) # Final stop command
            self.destroy_node()
            rclpy.shutdown()

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = KeyboardTeleop()
    
    try:
        tty.setraw(sys.stdin.fileno())
        node.run()
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        print("\nTerminal settings restored. Goodbye.")

if __name__ == '__main__':
    main()