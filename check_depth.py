#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import time

rclpy.init()
node = Node('depth_check')
qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL, history=HistoryPolicy.KEEP_LAST, depth=5)
bridge = CvBridge()
got = False

def cb(msg):
    global got
    if got:
        return
    got = True
    depth = bridge.imgmsg_to_cv2(msg, 'passthrough')
    valid = depth > 0
    if valid.any():
        dmin = depth[valid].min()
        dmax = depth[valid].max()
        dmean = depth[valid].mean()
        dmedian = np.median(depth[valid])
        below_3m = (depth[valid] < 3000).sum()
        below_5m = (depth[valid] < 5000).sum()
        total = valid.sum()
        print(f'depth (mm): min={dmin}, max={dmax}, mean={dmean:.0f}, median={dmedian:.0f}')
        print(f'below 3m: {below_3m}/{total} ({100*below_3m/total:.1f}%)')
        print(f'below 5m: {below_5m}/{total} ({100*below_5m/total:.1f}%)')
    else:
        print('no valid depth')

sub = node.create_subscription(Image, '/camera/camera/depth/image_rect_raw', cb, qos)
t0 = time.time()
while not got and time.time() - t0 < 8:
    rclpy.spin_once(node, timeout_sec=0.1)
node.destroy_node()
rclpy.shutdown()
