#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== TF: map -> odom ==="
timeout 3 ros2 run tf2_ros tf2_echo map odom 2>&1 | head -5
echo "=== TF: odom -> camera_link ==="
timeout 3 ros2 run tf2_ros tf2_echo odom camera_link 2>&1 | head -5
echo "=== TF: camera_link -> camera_depth_optical_frame ==="
timeout 3 ros2 run tf2_ros tf2_echo camera_link camera_depth_optical_frame 2>&1 | head -5
echo "=== Depth Points Hz ==="
timeout 5 ros2 topic hz /camera/depth/points --window 5 2>&1 | tail -3
echo "=== Odom Hz ==="
timeout 5 ros2 topic hz /odom --window 5 2>&1 | tail -3
