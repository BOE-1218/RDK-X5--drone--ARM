#!/usr/bin/env python3
"""监控 odom 更新频率和运动检测拒绝情况"""
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import time

class OdomMonitor(Node):
    def __init__(self):
        super().__init__('odom_monitor')
        self.last_pos = None
        self.last_time = time.time()
        self.count = 0
        self.reject_count = 0
        self.create_subscription(Odometry, '/odom', self.cb, 10)

    def cb(self, msg):
        self.count += 1
        now = time.time()
        pos = msg.pose.pose.position
        if self.last_pos is not None:
            dx = pos.x - self.last_pos.x
            dy = pos.y - self.last_pos.y
            dz = pos.z - self.last_pos.z
            dt = now - self.last_time
            moved = (dx*dx + dy*dy + dz*dz) ** 0.5
            if self.count % 5 == 0:
                print(f"[{self.count}] pos=({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f}) "
                      f"moved={moved:.4f}m dt={dt:.3f}s")
        else:
            print(f"[{self.count}] FIRST pos=({pos.x:.3f}, {pos.y:.3f}, {pos.z:.3f})")
        self.last_pos = pos
        self.last_time = now

rclpy.init()
node = OdomMonitor()
print("=== Monitoring /odom for 15 seconds (rotate camera now) ===")
end = time.time() + 15
while time.time() < end:
    rclpy.spin_once(node, timeout_sec=0.1)
print(f"\nTotal odom messages: {node.count}")
node.destroy_node()
rclpy.shutdown()

