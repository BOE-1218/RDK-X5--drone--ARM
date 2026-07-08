#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== CameraInfo ==="
ros2 topic echo /camera_info --once 2>&1 | head -15
echo "=== Depth CameraInfo ==="
ros2 topic echo /camera/camera/depth/camera_info --once 2>&1 | head -15
echo "=== RGB QoS ==="
ros2 topic info /image_raw -v 2>&1 | head -20
echo "=== Depth QoS ==="
ros2 topic info /camera/camera/depth/image_rect_raw -v 2>&1 | head -20
echo "=== TF ==="
ros2 run tf2_ros tf2_echo map camera_link 2>&1 | head -5 &
P=$!
sleep 2
kill $P 2>/dev/null
ros2 run tf2_ros tf2_echo usb_cam_link camera_depth_optical_frame 2>&1 | head -5 &
P=$!
sleep 2
kill $P 2>/dev/null
