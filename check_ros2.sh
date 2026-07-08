#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Nodes ==="
ros2 node list
echo "=== ColorPoints Info ==="
ros2 topic info /camera/depth/color_points
echo "=== CloudMap Info ==="
ros2 topic info /cloud_map
echo "=== TF Tree ==="
ros2 run tf2_tools view_frames 2>&1 &
PID=$!
sleep 4
kill $PID 2>/dev/null
cat /tmp/frames.txt 2>/dev/null || echo "no frames file"
