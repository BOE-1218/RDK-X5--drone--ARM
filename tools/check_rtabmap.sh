#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
# 停掉依赖 RGB 的节点
pkill -f rgbd_odometry 2>/dev/null
pkill -f rgb_depth_fusion 2>/dev/null
pkill -f octomap_server 2>/dev/null
sleep 2
echo "=== rtabmap_odom executables ==="
ls /opt/ros/humble/lib/rtabmap_odom/
echo "=== rtabmap_slam executables ==="
ls /opt/ros/humble/lib/rtabmap_slam/
