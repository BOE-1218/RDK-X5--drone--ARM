#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== ColorPoints Hz ==="
ros2 topic hz /camera/depth/color_points --window 3 2>&1 | head -5 &
PID=$!
sleep 4
kill $PID 2>/dev/null
echo "=== CloudMap Hz ==="
ros2 topic hz /cloud_map --window 3 2>&1 | head -5 &
PID=$!
sleep 4
kill $PID 2>/dev/null
