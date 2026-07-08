#!/usr/bin/env python3
"""
RGB + Depth 融合节点.
将 USB 摄像头的 RGB 图像和 RealSense 深度图对齐, 生成 XYZRGB 彩色点云.

假设: RGB 和深度图像分辨率相同 (640x480), 且近似共轴放置.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from cv_bridge import CvBridge
import numpy as np


class RGBDepthFusionNode(Node):
    def __init__(self):
        super().__init__('rgb_depth_fusion')

        self.declare_parameter('depth_scale', 0.001)
        self.declare_parameter('max_depth', 5.0)
        self.declare_parameter('min_depth', 0.3)

        self.depth_scale = self.get_parameter('depth_scale').value
        self.max_depth = self.get_parameter('max_depth').value
        self.min_depth = self.get_parameter('min_depth').value

        self.bridge = CvBridge()
        self.rgb_msg = None
        self.depth_msg = None
        self.camera_info = None
        self.fuse_count = 0

        self.rgb_sub = self.create_subscription(
            Image, '/image_raw', self.rgb_callback, 10)
        self.depth_sub = self.create_subscription(
            Image, '/camera/camera/depth/image_rect_raw', self.depth_callback, 10)
        self.info_sub = self.create_subscription(
            CameraInfo, '/camera/camera/depth/camera_info', self.info_callback, 10)

        self.cloud_pub = self.create_publisher(
            PointCloud2, '/camera/depth/color_points', 10)

        self.timer = self.create_timer(0.1, self.fuse_callback)

        self.get_logger().info('RGBDepthFusion started. Waiting for RGB + Depth...')

    def rgb_callback(self, msg):
        self.rgb_msg = msg
        self.get_logger().debug('RGB received')

    def depth_callback(self, msg):
        self.depth_msg = msg
        self.get_logger().debug('Depth received')

    def info_callback(self, msg):
        self.camera_info = msg
        self.get_logger().debug('CameraInfo received')

    def fuse_callback(self):
        if self.rgb_msg is None:
            self.get_logger().debug('Waiting for RGB...')
            return
        if self.depth_msg is None:
            self.get_logger().debug('Waiting for Depth...')
            return
        if self.camera_info is None:
            self.get_logger().debug('Waiting for CameraInfo...')
            return

        try:
            rgb_cv = self.bridge.imgmsg_to_cv2(self.rgb_msg, desired_encoding='rgb8')
            depth_cv = self.bridge.imgmsg_to_cv2(self.depth_msg, desired_encoding='passthrough')
        except Exception as e:
            self.get_logger().error(f'CVBridge error: {e}')
            return

        h, w = depth_cv.shape
        if rgb_cv.shape[0] != h or rgb_cv.shape[1] != w:
            import cv2
            rgb_cv = cv2.resize(rgb_cv, (w, h))

        K = np.array(self.camera_info.k).reshape(3, 3)
        fx, fy = K[0, 0], K[1, 1]
        cx, cy = K[0, 2], K[1, 2]

        u, v = np.meshgrid(np.arange(w), np.arange(h))
        z = depth_cv.astype(np.float32) * self.depth_scale

        valid = (z > self.min_depth) & (z < self.max_depth)
        z = z[valid]
        u = u[valid]
        v = v[valid]

        if len(z) == 0:
            self.get_logger().debug('No valid depth points')
            return

        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        rgb = rgb_cv[valid]
        r = rgb[:, 0].astype(np.uint32)
        g = rgb[:, 1].astype(np.uint32)
        b = rgb[:, 2].astype(np.uint32)
        rgb_packed = (r << 16) | (g << 8) | b

        points = np.zeros((len(x), 6), dtype=np.float32)
        points[:, 0] = x
        points[:, 1] = y
        points[:, 2] = z
        points[:, 3:] = rgb_packed.reshape(-1, 1).astype(np.float32)

        cloud_msg = PointCloud2()
        cloud_msg.header = self.depth_msg.header
        cloud_msg.header.frame_id = self.camera_info.header.frame_id
        cloud_msg.height = 1
        cloud_msg.width = len(x)
        cloud_msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='rgb', offset=12, datatype=PointField.FLOAT32, count=1),
        ]
        cloud_msg.is_bigendian = False
        cloud_msg.point_step = 16
        cloud_msg.row_step = cloud_msg.point_step * len(x)
        cloud_msg.is_dense = True
        cloud_msg.data = points.tobytes()

        self.cloud_pub.publish(cloud_msg)
        self.fuse_count += 1
        if self.fuse_count % 10 == 0:
            self.get_logger().info(f'Published {self.fuse_count} color pointclouds, points={len(x)}')


def main():
    rclpy.init()
    node = RGBDepthFusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
