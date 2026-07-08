#!/usr/bin/env python3
"""
远程键盘控制 odom 节点 (运行在远程设备上).
通过订阅 /odom_cmd 话题接收控制命令, 发布 odom->camera_link TF.

控制命令格式 (geometry_msgs/Twist):
  linear.x: 前进/后退 (米)
  angular.z: 旋转 (弧度)

本地通过 ros2 topic pub 发送命令:
  ros2 topic pub --once /odom_cmd geometry_msgs/Twist '{linear: {x: 0.1}, angular: {z: 0.0}}'
"""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Twist
from tf2_ros import TransformBroadcaster
import math


class RemoteOdomNode(Node):
    def __init__(self):
        super().__init__('remote_odom_node')

        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('publish_rate', 30.0)

        self.frame_id = self.get_parameter('frame_id').value
        self.odom_frame_id = self.get_parameter('odom_frame_id').value
        self.publish_tf = self.get_parameter('publish_tf').value
        self.publish_rate = self.get_parameter('publish_rate').value

        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # 订阅控制命令
        self.cmd_sub = self.create_subscription(
            Twist, '/odom_cmd', self.cmd_callback, 10)

        # 定时发布 odom
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_odom)

        self.get_logger().info(
            f'RemoteOdomNode started. Subscribe /odom_cmd (Twist). '
            f'linear.x=translation, angular.z=rotation')

    def cmd_callback(self, msg):
        dx = msg.linear.x
        dy = msg.linear.y
        dtheta = msg.angular.z

        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)
        self.x += dx * cos_t - dy * sin_t
        self.y += dx * sin_t + dy * cos_t
        self.theta += dtheta
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        self.get_logger().info(
            f'Cmd: dx={dx:.3f}, dy={dy:.3f}, dtheta={math.degrees(dtheta):.1f}deg, '
            f'pose=({self.x:.2f},{self.y:.2f},{math.degrees(self.theta):.1f}deg)')

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
        odom.pose.covariance[0] = 0.001
        odom.pose.covariance[7] = 0.001
        odom.pose.covariance[35] = 0.001
        self.odom_pub.publish(odom)


def main():
    rclpy.init()
    node = RemoteOdomNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
