#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Topics ==="
ros2 topic list | grep -E "image_raw|depth|camera_info"
echo "=== Depth Hz ==="
ros2 topic hz /camera/camera/depth/image_rect_raw --window 5 2>&1 &
PID1=$!
echo "=== RGB Hz ==="
ros2 topic hz /image_raw --window 5 2>&1 &
PID2=$!
sleep 5
kill $PID1 $PID2 2>/dev/null
