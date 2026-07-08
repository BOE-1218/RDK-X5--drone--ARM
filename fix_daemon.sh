#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
ros2 daemon stop
sleep 1
ros2 daemon start
sleep 2
echo "=== Nodes ==="
ros2 node list
echo "=== Topics ==="
ros2 topic list
