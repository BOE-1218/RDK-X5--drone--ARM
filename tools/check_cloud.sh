#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== ColorPoints echo ==="
ros2 topic echo /camera/depth/color_points --once 2>&1 | head -20 &
PID=$!
sleep 3
kill $PID 2>/dev/null
echo "=== CloudMap echo ==="
ros2 topic echo /cloud_map --once 2>&1 | head -20 &
PID=$!
sleep 3
kill $PID 2>/dev/null
