#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== ColorPoints ==="
ros2 topic hz /camera/depth/color_points --window 10 &
PID=$!
sleep 8
kill $PID 2>/dev/null
echo "=== CloudMap ==="
ros2 topic hz /cloud_map --window 10 &
PID=$!
sleep 8
kill $PID 2>/dev/null
echo "=== ImageRaw ==="
ros2 topic hz /image_raw --window 10 &
PID=$!
sleep 5
kill $PID 2>/dev/null
