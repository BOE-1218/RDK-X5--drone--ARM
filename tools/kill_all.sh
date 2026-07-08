#!/bin/bash
# 杀掉所有旧进程 (不影响 SSH 连接)
pkill -f realsense2_camera_node 2>/dev/null
pkill -f 'ros2 launch' 2>/dev/null
pkill -f v4l2_camera 2>/dev/null
pkill -f rgbd_odometry 2>/dev/null
pkill -f icp_odometry 2>/dev/null
pkill -f depth_visual_odom 2>/dev/null
pkill -f depth_odom 2>/dev/null
pkill -f point_cloud_xyz 2>/dev/null
pkill -f depth_image_proc 2>/dev/null
pkill -f octomap_server_node 2>/dev/null
pkill -f rviz2 2>/dev/null
pkill -f x11vnc 2>/dev/null
pkill -f Xvfb 2>/dev/null
pkill -f static_transform_publisher 2>/dev/null
sleep 2
echo "All processes killed"
