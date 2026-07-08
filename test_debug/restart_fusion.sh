#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
pkill -f rgb_depth_fusion
sleep 1
python3 /tmp/rgb_depth_fusion.py > /tmp/fusion.log 2>&1 &
sleep 5
cat /tmp/fusion.log
