#!/usr/bin/env python3
"""检查深度图稳定性: 连续采集 30 帧, 统计像素变化."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import time

rclpy.init()
node = Node("depth_stability_check")
frames = []

def cb(msg):
    arr = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
    frames.append(arr.copy())

sub = node.create_subscription(Image, "/camera/camera/depth/image_rect_raw", cb, 10)
start = time.time()
while len(frames) < 30 and time.time() - start < 5:
    rclpy.spin_once(node, timeout_sec=0.1)

if len(frames) >= 2:
    print(f"Collected {len(frames)} frames")
    # 比较第 1 帧和后续帧
    base = frames[0].astype(np.float64)
    valid_base = base > 0
    print(f"Base frame valid pixels: {np.sum(valid_base)}")
    for i in range(1, min(len(frames), 10)):
        curr = frames[i].astype(np.float64)
        valid_curr = curr > 0
        valid_both = valid_base & valid_curr
        if np.sum(valid_both) > 0:
            diff = np.abs(base[valid_both] - curr[valid_both])
            print(f"Frame {i}: valid={np.sum(valid_both)}, "
                  f"mean_diff={diff.mean():.1f}mm, "
                  f"max_diff={diff.max():.1f}mm, "
                  f"std_diff={diff.std():.1f}mm")
else:
    print(f"Only got {len(frames)} frames")

node.destroy_node()
rclpy.shutdown()
