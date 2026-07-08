#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Topics ==="
ros2 topic list | grep -E "color_points|cloud_map|image_raw"
echo "=== ColorPoints Hz ==="
ros2 topic hz /camera/depth/color_points --window 5 2>&1 | head -5 &
PID1=$!
echo "=== CloudMap Hz ==="
ros2 topic hz /cloud_map --window 5 2>&1 | head -5 &
PID2=$!
sleep 3
kill $PID1 $PID2 2>/dev/null
echo "=== TF ==="
ros2 run tf2_ros tf2_echo camera_depth_optical_frame map 2>&1 | head -5 &
PID3=$!
sleep 3
kill $PID3 2>/dev/null
