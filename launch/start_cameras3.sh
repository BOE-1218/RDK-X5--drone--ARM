#!/bin/bash
# RealSense D430: 仅深度
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 launch realsense2_camera rs_launch.py \
    enable_depth:=true \
    depth_module.depth_profile:=640x480x30 \
    pointcloud.enable:=true \
    pointcloud.allow_no_texture_points:=true \
    enable_infra1:=false \
    enable_infra2:=false \
    enable_color:=false \
    enable_sync:=false \
    temporal_filter.enable:=true \
    spatial_filter.enable:=true \
    hole_filling_filter.enable:=true \
    publish_tf:=false
