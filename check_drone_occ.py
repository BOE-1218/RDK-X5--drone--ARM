#!/usr/bin/env python3
"""检查 odom 当前位置在 occupancy grid 中是否被标记为障碍物"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry
import struct
import math

class DroneOccChecker(Node):
    def __init__(self):
        super().__init__('drone_occ_checker')
        self.odom = None
        self.occ = None
        self.occ_inflate = None
        self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.create_subscription(PointCloud2, '/grid_map/occupancy', self.occ_cb, 10)
        self.create_subscription(PointCloud2, '/grid_map/occupancy_inflate', self.inflate_cb, 10)

    def odom_cb(self, msg):
        self.odom = msg

    def occ_cb(self, msg):
        if self.occ is None:
            self.occ = msg

    def inflate_cb(self, msg):
        if self.occ_inflate is None:
            self.occ_inflate = msg

    def check(self):
        if self.odom is None:
            print("No odom received!")
            return
        if self.occ_inflate is None:
            print("No occupancy_inflate received!")
            return

        px = self.odom.pose.pose.position.x
        py = self.odom.pose.pose.position.y
        pz = self.odom.pose.pose.position.z
        print(f"Drone position: ({px:.3f}, {py:.3f}, {pz:.3f})")

        # 解析 occupancy_inflate 点
        points = []
        for i in range(self.occ_inflate.width):
            offset = i * self.occ_inflate.point_step
            x, y, z = struct.unpack_from('<fff', self.occ_inflate.data, offset)
            dist = math.sqrt((x-px)**2 + (y-py)**2 + (z-pz)**2)
            points.append((dist, x, y, z))
        points.sort()

        print(f"\noccupancy_inflate: {len(points)} points")
        print(f"\n=== 10 closest points to drone ===")
        for dist, x, y, z in points[:10]:
            print(f"  dist={dist:.3f}  ({x:.3f}, {y:.3f}, {z:.3f})")

        close = sum(1 for d, _, _, _ in points if d < 0.3)
        print(f"\nPoints within 0.3m of drone: {close}")
        close5 = sum(1 for d, _, _, _ in points if d < 0.5)
        print(f"Points within 0.5m of drone: {close5}")

        # 也检查 occupancy (non-inflate)
        if self.occ is not None:
            occ_points = []
            for i in range(self.occ.width):
                offset = i * self.occ.point_step
                x, y, z = struct.unpack_from('<fff', self.occ.data, offset)
                dist = math.sqrt((x-px)**2 + (y-py)**2 + (z-pz)**2)
                occ_points.append((dist, x, y, z))
            occ_points.sort()
            print(f"\noccupancy (non-inflate): {len(occ_points)} points")
            print(f"=== 5 closest to drone ===")
            for dist, x, y, z in occ_points[:5]:
                print(f"  dist={dist:.3f}  ({x:.3f}, {y:.3f}, {z:.3f})")

rclpy.init()
node = DroneOccChecker()
import time
end = time.time() + 8
while time.time() < end and (node.odom is None or node.occ_inflate is None):
    rclpy.spin_once(node, timeout_sec=0.2)
node.check()
node.destroy_node()
rclpy.shutdown()

