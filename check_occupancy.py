#!/usr/bin/env python3
"""检查 occupancy grid 点云内容, 找出靠近原点的障碍物"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
import struct
import math

class OccChecker(Node):
    def __init__(self):
        super().__init__('occ_checker')
        self.sub = self.create_subscription(
            PointCloud2, '/grid_map/occupancy_inflate', self.cb, 10)
        self.got = False

    def cb(self, msg):
        if self.got:
            return
        self.got = True
        print(f"frame: {msg.header.frame_id}, width: {msg.width}, point_step: {msg.point_step}")
        # 解析点
        points = []
        for i in range(msg.width):
            offset = i * msg.point_step
            x, y, z = struct.unpack_from('<fff', msg.data, offset)
            points.append((x, y, z))
        # 按距离原点排序
        points_with_dist = [(math.sqrt(x*x+y*y+z*z), x, y, z) for x, y, z in points]
        points_with_dist.sort()
        print(f"\nTotal points: {len(points)}")
        print("\n=== 10 closest points to origin ===")
        for dist, x, y, z in points_with_dist[:10]:
            print(f"  dist={dist:.3f}  ({x:.3f}, {y:.3f}, {z:.3f})")
        print("\n=== 5 farthest points ===")
        for dist, x, y, z in points_with_dist[-5:]:
            print(f"  dist={dist:.3f}  ({x:.3f}, {y:.3f}, {z:.3f})")
        # 统计
        dists = [d for d, _, _, _ in points_with_dist]
        if dists:
            print(f"\nDist stats: min={min(dists):.3f}, max={max(dists):.3f}, median={sorted(dists)[len(dists)//2]:.3f}")
            close = sum(1 for d in dists if d < 0.5)
            print(f"Points within 0.5m of origin: {close}")

rclpy.init()
node = OccChecker()
import time
end = time.time() + 6
while time.time() < end and not node.got:
    rclpy.spin_once(node, timeout_sec=0.2)
if not node.got:
    print("No occupancy_inflate message received!")
node.destroy_node()
rclpy.shutdown()

