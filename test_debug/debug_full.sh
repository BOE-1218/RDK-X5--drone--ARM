#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Processes ==="
ps aux | grep -E "realsense|v4l2|rgbd_odometry|rgb_depth|octomap" | grep -v grep | awk '{print $2, $11, $12, $13}'
echo "=== RGB Hz ==="
timeout 5 ros2 topic hz /image_raw --window 5 2>&1 | tail -3
echo "=== Depth Hz ==="
timeout 5 ros2 topic hz /camera/camera/depth/image_rect_raw --window 5 2>&1 | tail -3
echo "=== RGB Header ==="
timeout 3 ros2 topic echo /image_raw --once --field header 2>&1
echo "=== Depth Header ==="
timeout 3 ros2 topic echo /camera/camera/depth/image_rect_raw --once --field header 2>&1
