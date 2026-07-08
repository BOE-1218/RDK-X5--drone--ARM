#!/usr/bin/env python3
"""
键盘遥控里程计节点.
通过键盘按键发布 odom->camera_link TF, 完全避免 ICP 漂移.

操作:
  W/上: 前进 0.1m
  S/下: 后退 0.1m
  A/左: 左转 10度
  D/右: 右转 10度
  Q:    左平移 0.1m
  E:    右平移 0.1m
  R:    重置位姿
  空格:  停止
"""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Twist
from tf2_ros import TransformBroadcaster
import math
import sys
import termios
import tty
import select


def get_key(timeout=0.1):
    """非阻塞读取键盘输入."""
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    return key


class KeyboardOdomNode(Node):
    def __init__(self):
        super().__init__('keyboard_odom_node')

        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('linear_step', 0.1)
        self.declare_parameter('angular_step', 0.1745)  # 10 度

        self.frame_id = self.get_parameter('frame_id').value
        self.odom_frame_id = self.get_parameter('odom_frame_id').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.linear_step = self.get_parameter('linear_step').value
        self.angular_step = self.get_parameter('angular_step').value

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # 定时读取键盘
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.last_publish_time = self.get_clock().now()

        self.get_logger().info(
            f'KeyboardOdomNode started. '
            f'linear_step={self.linear_step}m, angular_step={math.degrees(self.angular_step):.1f}deg')
        self.get_logger().info('Controls: W/S=前后, A/D=转向, Q/E=平移, R=重置, 空格=停止, Ctrl+C=退出')
        self.get_logger().info('IMPORTANT: 在运行此节点的终端中按键才有效!')

    def timer_callback(self):
        key = get_key(0.05)

        dx = 0.0
        dy = 0.0
        dtheta = 0.0
        cmd_msg = Twist()

        if key:
            key_lower = key.lower()
            if key_lower == 'w':
                dx = self.linear_step
                cmd_msg.linear.x = self.linear_step
                self.get_logger().info(f'Forward {self.linear_step}m')
            elif key_lower == 's':
                dx = -self.linear_step
                cmd_msg.linear.x = -self.linear_step
                self.get_logger().info(f'Backward {self.linear_step}m')
            elif key_lower == 'a':
                dtheta = self.angular_step
                cmd_msg.angular.z = self.angular_step
                self.get_logger().info(f'Turn left {math.degrees(self.angular_step):.1f}deg')
            elif key_lower == 'd':
                dtheta = -self.angular_step
                cmd_msg.angular.z = -self.angular_step
                self.get_logger().info(f'Turn right {math.degrees(self.angular_step):.1f}deg')
            elif key_lower == 'q':
                dy = self.linear_step
                cmd_msg.linear.y = self.linear_step
                self.get_logger().info(f'Strafe left {self.linear_step}m')
            elif key_lower == 'e':
                dy = -self.linear_step
                cmd_msg.linear.y = -self.linear_step
                self.get_logger().info(f'Strafe right {self.linear_step}m')
            elif key_lower == 'r':
                self.x = 0.0
                self.y = 0.0
                self.theta = 0.0
                self.get_logger().info('Pose reset to origin')
            elif key == ' ':
                self.get_logger().info('Stop')
            elif key == '\x03':  # Ctrl+C
                self.get_logger().info('Exiting...')
                rclpy.shutdown()
                return

        # 更新位姿
        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)
        self.x += dx * cos_t - dy * sin_t
        self.y += dx * sin_t + dy * cos_t
        self.theta += dtheta
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # 发布 cmd_vel
        self.cmd_vel_pub.publish(cmd_msg)

        # 发布 odom 和 TF
        self.publish_odom()

    def publish_odom(self):
        now = self.get_clock().now()

        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = now.to_msg()
            t.header.frame_id = self.odom_frame_id
            t.child_frame_id = self.frame_id
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.z = math.sin(self.theta / 2.0)
            t.transform.rotation.w = math.cos(self.theta / 2.0)
            self.tf_broadcaster.sendTransform(t)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame_id
        odom.child_frame_id = self.frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        odom.pose.covariance[0] = 0.001  # 高置信度
        odom.pose.covariance[7] = 0.001
        odom.pose.covariance[35] = 0.001
        self.odom_pub.publish(odom)


def main():
    rclpy.init()
    node = KeyboardOdomNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
