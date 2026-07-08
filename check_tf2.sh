#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== TF List ==="
ros2 run tf2_tools view_frames 2>&1 &
PID=$!
sleep 5
kill $PID 2>/dev/null
echo "=== TF Frames ==="
ros2 topic echo /tf --once 2>&1 | head -20 &
PID=$!
sleep 3
kill $PID 2>/dev/null
echo "=== Odom Topic ==="
ros2 topic info /odom
echo "=== Odom Echo ==="
timeout 3 ros2 topic echo /odom --once 2>&1 | head -10
