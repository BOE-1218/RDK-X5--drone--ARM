#!/usr/bin/env python3
"""Check if depth and odom timestamps are synchronized."""
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
import time

rclpy.init()
node = Node('sync_check')

qos_depth = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=5
)

latest_depth_stamp = None
latest_odom_stamp = None
depth_count = 0
odom_count = 0

def depth_cb(msg):
    global latest_depth_stamp, depth_count
    latest_depth_stamp = msg.header.stamp
    depth_count += 1

def odom_cb(msg):
    global latest_odom_stamp, odom_count
    latest_odom_stamp = msg.header.stamp
    odom_count += 1

node.create_subscription(Image, '/camera/camera/depth/image_rect_raw', depth_cb, qos_depth)
node.create_subscription(Odometry, '/odom', odom_cb, 10)

t0 = time.time()
while time.time() - t0 < 5:
    rclpy.spin_once(node, timeout_sec=0.1)
    if latest_depth_stamp and latest_odom_stamp:
        d_sec = latest_depth_stamp.sec + latest_depth_stamp.nanosec * 1e-9
        o_sec = latest_odom_stamp.sec + latest_odom_stamp.nanosec * 1e-9
        diff = abs(d_sec - o_sec)
        print(f'depth stamp: {latest_depth_stamp.sec}.{latest_depth_stamp.nanosec:09d}')
        print(f'odom stamp:  {latest_odom_stamp.sec}.{latest_odom_stamp.nanosec:09d}')
        print(f'diff: {diff*1000:.1f} ms')
        print(f'counts: depth={depth_count}, odom={odom_count}')
        break

node.destroy_node()
rclpy.shutdown()
