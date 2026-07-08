#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Topic List ==="
ros2 topic list
echo "=== CameraInfo Topic ==="
ros2 topic info /camera_info -v 2>&1 | head -20
echo "=== Depth CameraInfo ==="
ros2 topic info /camera/camera/depth/camera_info -v 2>&1 | head -20
echo "=== Image QoS ==="
ros2 topic info /image_raw -v 2>&1 | head -20
echo "=== Depth QoS ==="
ros2 topic info /camera/camera/depth/image_rect_raw -v 2>&1 | head -20
