#!/bin/bash
# 启动深度视觉里程计
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
python3 /tmp/depth_odom.py
