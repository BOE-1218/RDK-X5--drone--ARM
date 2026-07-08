#!/bin/bash
# RTAB-Map RGB-D 里程计（使用红外图代替 RGB）
# 红外图和深度图完全对齐（同一物理传感器），无需 USB 摄像头
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

ros2 run rtabmap_odom rgbd_odometry \
    --ros-args \
    -r rgb/image:=/camera/camera/infra1/image_rect_raw \
    -r depth/image:=/camera/camera/depth/image_rect_raw \
    -r rgb/camera_info:=/camera/camera/infra1/camera_info \
    -p frame_id:=camera_depth_optical_frame \
    -p odom_frame_id:=odom \
    -p publish_tf:=true \
    -p publish_odom:=true \
    -p approx_sync:=true \
    -p approx_sync_max_interval:=0.5 \
    -p queue_size:=10 \
    -p vis/feature_type:=6 \
    -p vis/max_features:=100 \
    -p vis/min_inliers:=15 \
    -p odom/keyframe_strategy:=0 \
    -p odom_guess_motion:=true \
    -p odom_filtering_strategy:=1
