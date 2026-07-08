#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Infra Hz ==="
timeout 5 ros2 topic hz /camera/camera/infra1/image_rect_raw --window 5 2>&1 | tail -3
echo "=== Depth Hz ==="
timeout 5 ros2 topic hz /camera/camera/depth/image_rect_raw --window 5 2>&1 | tail -3
echo "=== Infra QoS ==="
ros2 topic info /camera/camera/infra1/image_rect_raw -v 2>&1 | head -20
echo "=== Depth QoS ==="
ros2 topic info /camera/camera/depth/image_rect_raw -v 2>&1 | head -20
echo "=== Infra Header ==="
timeout 3 ros2 topic echo /camera/camera/infra1/image_rect_raw --once --field header 2>&1
echo "=== Depth Header ==="
timeout 3 ros2 topic echo /camera/camera/depth/image_rect_raw --once --field header 2>&1
