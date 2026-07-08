#!/bin/bash
# 重启 depth_odom 和 EgoPlanner，重置里程计原点
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1

echo "=== 重启 depth_odom ==="
pkill -9 -f '/tmp/depth_odom.py' 2>/dev/null
sleep 2
nohup python3 /tmp/depth_odom.py > /tmp/depth_odom.log 2>&1 &
echo "depth_odom PID=$!"
sleep 5

echo "=== 新 odom 位置 ==="
timeout 3 ros2 topic echo /odom --once 2>&1 | grep -A4 'position:' | head -6

echo "=== 重启 EgoPlanner ==="
pkill -9 -f 'ego_planner_node' 2>/dev/null
sleep 2
nohup bash /tmp/start_ego.sh > /tmp/ego_planner.log 2>&1 &
echo "ego_planner PID=$!"
sleep 8

echo "=== EgoPlanner occupancy ==="
timeout 5 ros2 topic echo /grid_map/occupancy --once 2>&1 | head -10

echo "=== OctoMap occupied_voxels ==="
timeout 5 ros2 topic echo /occupied_voxels --once 2>&1 | head -8

echo "=== 深度数据范围 (中心像素) ==="
python3 -c "
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
rclpy.init()
n = Node('check')
bridge = CvBridge()
result = {'done': False}
def cb(msg):
    if result['done']: return
    d = bridge.imgmsg_to_cv2(msg, 'passthrough')
    arr = d.astype(np.float32) * 0.001
    valid = (arr > 0.1) & (arr < 10.0)
    if valid.any():
        print(f'深度统计: min={arr[valid].min():.3f}m, max={arr[valid].max():.3f}m, median={np.median(arr[valid]):.3f}m')
        print(f'有效像素: {valid.sum()}/{arr.size} ({100*valid.sum()/arr.size:.1f}%)')
        h, w = arr.shape
        center = arr[h//2-50:h//2+50, w//2-50:w//2+50]
        cvalid = (center > 0.1) & (center < 10.0)
        if cvalid.any():
            print(f'中心区域: min={center[cvalid].min():.3f}m, max={center[cvalid].max():.3f}m, median={np.median(center[cvalid]):.3f}m')
        print(f'近处像素 (<2m): {((arr > 0.1) & (arr < 2.0)).sum()} ({100*((arr > 0.1) & (arr < 2.0)).sum()/arr.size:.1f}%)')
        print(f'近处像素 (<5m): {((arr > 0.1) & (arr < 5.0)).sum()} ({100*((arr > 0.1) & (arr < 5.0)).sum()/arr.size:.1f}%)')
    result['done'] = True
n.create_subscription(Image, '/camera/camera/depth/image_rect_raw', cb, 10)
import time
end = time.time() + 5
while not result['done'] and time.time() < end:
    rclpy.spin_once(n, timeout_sec=0.1)
n.destroy_node()
rclpy.shutdown()
"

echo "=== 完成 ==="
