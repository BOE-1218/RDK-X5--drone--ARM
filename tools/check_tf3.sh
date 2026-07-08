#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== All TF frames ==="
ros2 run tf2_tools view_frames 2>&1 &
PID=$!
sleep 5
kill $PID 2>/dev/null
echo "=== /tf topics ==="
ros2 topic list | grep tf
echo "=== /tf echo ==="
timeout 3 ros2 topic echo /tf --once 2>&1 | head -30
echo "=== /tf_static echo ==="
timeout 3 ros2 topic echo /tf_static --once 2>&1 | head -30
