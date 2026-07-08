#!/bin/bash
# RealSense D430: 深度 + 红外1（不使用硬件同步）
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 launch realsense2_camera rs_launch.py \
    enable_depth:=true \
    depth_module.depth_profile:=640x480x30 \
    enable_infra1:=true \
    enable_infra2:=false \
    pointcloud.enable:=false \
    enable_color:=false \
    enable_sync:=false \
    temporal_filter.enable:=true \
    spatial_filter.enable:=true \
    hole_filling_filter.enable:=true
