#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Odom Info ==="
ros2 topic info /odom -v
echo "=== Odom Echo ==="
timeout 5 ros2 topic echo /odom --once 2>&1 | head -20
echo "=== ICP Log tail ==="
tail -20 /tmp/icp_odom.log
