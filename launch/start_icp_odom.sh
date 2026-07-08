#!/bin/bash
# RTAB-Map ICP 里程计 (修正版)
# 输入: /camera/depth/points (深度点云)
# 输出: odom -> camera_depth_optical_frame 动态 TF + /odom 话题
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 run rtabmap_odom icp_odometry \
    --ros-args \
    -r scan_cloud:=/camera/depth/points \
    -p frame_id:=camera_depth_optical_frame \
    -p odom_frame_id:=odom \
    -p publish_tf:=true \
    -p publish_odom:=true \
    -p queue_size:=10 \
    -p ICP/max_correspondence_distance:=0.1 \
    -p ICP/iterations:=30 \
    -p ICP/voxel_size:=0.05 \
    -p ICP/downsampling:=true \
    -p odom_guess_motion:=true \
    -p odom_filtering_strategy:=1
