#!/bin/bash
. /opt/ros/humble/setup.bash
export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
export ROS_LOCALHOST=1
nohup rviz2 -d /tmp/pointcloud.rviz > /tmp/rviz2.log 2>&1 &
sleep 6
cat /tmp/rviz2.log
