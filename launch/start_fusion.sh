#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
python3 /tmp/rgb_depth_fusion.py
