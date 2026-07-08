#!/bin/bash
# depth_image_proc: 深度图 -> XYZ 点云
# 输入: /camera/camera/depth/image_rect_raw + /camera/camera/depth/camera_info
# 输出: /camera/depth/points (PointCloud2, XYZ only)
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 run depth_image_proc point_cloud_xyz_node \
    --ros-args \
    -r image_rect:=/camera/camera/depth/image_rect_raw \
    -r camera_info:=/camera/camera/depth/camera_info \
    -r points:=/camera/depth/points \
    -p use_depth:=true \
    -p queue_size:=10
