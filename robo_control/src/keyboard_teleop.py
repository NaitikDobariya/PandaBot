#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty

msg = """
Control Your Robot (WASD)
---------------------------
w : forward
x : backward
a : left
d : right
s/space : stop

CTRL-C to quit
"""

class KeyboardTeleop(Node):

    def __init__(self):
        super().__init__('keyboard_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.linear_speed = 0.3
        self.angular_speed = 0.8

        print(msg)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)

        key = ''
        if rlist:
            key = sys.stdin.read(1)

            # Handle arrow keys (escape sequence)
            if key == '\x1b':
                sys.stdin.read(2)  # discard rest
                return ''

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()
                twist = Twist()

                if key == 'w':
                    twist.linear.x = self.linear_speed
                elif key == 'x':
                    twist.linear.x = -self.linear_speed
                elif key == 'a':
                    twist.angular.z = self.angular_speed
                elif key == 'd':
                    twist.angular.z = -self.angular_speed
                elif key in ['s', ' ']:
                    twist = Twist()
                elif key == '\x03':
                    break
                else:
                    continue

                self.pub.publish(twist)

                print(f"\rLinear: {twist.linear.x:.2f} | Angular: {twist.angular.z:.2f}", end="")

        except Exception as e:
            print(e)

        finally:
            self.pub.publish(Twist())
            self.destroy_node()
            rclpy.shutdown()
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = KeyboardTeleop()
    node.run()


if __name__ == '__main__':
    main()