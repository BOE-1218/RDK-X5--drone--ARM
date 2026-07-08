#!/bin/bash
# RTAB-Map RGB-D 视觉里程计
# 输入: RGB /image_raw + Depth /camera/camera/depth/image_rect_raw + CameraInfo
# 输出: odom -> camera_link 动态 TF + /odom 话题
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 run rtabmap_odom rgbd_odometry \
    --ros-args \
    -r rgb/image:=/image_raw \
    -r depth/image:=/camera/camera/depth/image_rect_raw \
    -r rgb/camera_info:=/camera_info \
    -p frame_id:=camera_link \
    -p odom_frame_id:=odom \
    -p publish_tf:=true \
    -p publish_odom:=true \
    -p approx_sync:=true \
    -p approx_sync_max_interval:=0.5 \
    -p queue_size:=10 \
    -p vis/feature_type:=6 \
    -p vis/max_features:=150 \
    -p vis/min_inliers:=20 \
    -p odom/keyframe_strategy:=0 \
    -p odom/guess_motion:=true \
    -p odom/filtering_strategy:=1 \
    -p vis/corner_type:=0 \
    -p odom/strategy:=0

