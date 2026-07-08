#!/bin/bash
# OctoMap 八叉树建图
# 输入: /camera/depth/points (深度点云)
# 输出: /occupied_voxels, /octomap_full, /octomap_binary
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 run octomap_server octomap_server_node \
    --ros-args \
    -p resolution:=0.05 \
    -p frame_id:=odom \
    -p base_frame_id:=odom \
    -p pointcloud_min_z:=0.05 \
    -p pointcloud_max_z:=3.0 \
    -p occupancy_min_z:=0.05 \
    -p occupancy_max_z:=2.5 \
    -p sensor_model/max_range:=5.0 \
    -p sensor_model/min_range:=0.3 \
    -p pointcloud_max_x:=5.0 \
    -p pointcloud_min_x:=-5.0 \
    -p pointcloud_max_y:=5.0 \
    -p pointcloud_min_y:=-5.0 \
    -p filter_speckles:=true \
    -p use_color:=false \
    -r cloud_in:=/camera/depth/points
