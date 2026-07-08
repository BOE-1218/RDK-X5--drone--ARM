#!/usr/bin/env python3
"""检查深度图有效像素距离分布."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import time

rclpy.init()
node = Node('depth_check2')
msg_recv = [None]

def cb(msg):
    msg_recv[0] = msg

sub = node.create_subscription(Image, '/camera/camera/depth/image_rect_raw', cb, 10)
start = time.time()
while msg_recv[0] is None and time.time() - start < 5:
    rclpy.spin_once(node, timeout_sec=0.1)

if msg_recv[0]:
    arr = np.frombuffer(msg_recv[0].data, dtype=np.uint16).astype(np.float32) / 1000.0
    valid = arr[arr > 0]
    print(f'Total pixels: {len(arr)}')
    print(f'Valid pixels: {len(valid)}')
    bins = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 100.0]
    for i in range(len(bins)-1):
        count = np.sum((valid >= bins[i]) & (valid < bins[i+1]))
        print(f'  {bins[i]:.1f}-{bins[i+1]:.1f}m: {count}')
    if len(valid) > 0:
        print(f'Min: {valid.min():.3f}m, Max: {valid.max():.3f}m, Mean: {valid.mean():.3f}m')

node.destroy_node()
rclpy.shutdown()
