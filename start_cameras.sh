#!/bin/bash
# 启动 RealSense D430 深度相机 + USB 摄像头
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

# RealSense D430 (深度 only)
ros2 launch realsense2_camera rs_launch.py \
    enable_depth:=true \
    depth_module.depth_profile:=640x480x30 \
    pointcloud.enable:=false \
    enable_infra:=false \
    enable_color:=false \
    enable_sync:=false \
    temporal_filter.enable:=true \
    spatial_filter.enable:=true \
    hole_filling_filter.enable:=true &

RS_PID=$!
sleep 3

# USB 摄像头 (RGB)
ros2 run v4l2_camera v4l2_camera_node \
    --ros-args \
    -p video_device:=/dev/video0 \
    -p image_size:=[640,480] \
    -p pixel_format:=YUYV \
    -p camera_frame_id:=usb_cam_link \
    -p output_encoding:=rgb8 &

USB_PID=$!

# 创建 USB 摄像头标定文件
mkdir -p /root/.ros/camera_info
cat > /root/.ros/camera_info/usb2.0_pc_camera.yaml << 'CALIB'
image_width: 640
image_height: 480
camera_name: usb2.0_pc_camera
camera_matrix:
  rows: 3
  cols: 3
  data: [400.0, 0.0, 320.0, 0.0, 400.0, 240.0, 0.0, 0.0, 1.0]
distortion_model: plumb_bob
distortion_coefficients:
  rows: 1
  cols: 5
  data: [0.0, 0.0, 0.0, 0.0, 0.0]
rectification_matrix:
  rows: 3
  cols: 3
  data: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
projection_matrix:
  rows: 3
  cols: 4
  data: [400.0, 0.0, 320.0, 0.0, 0.0, 400.0, 240.0, 0.0, 0.0, 0.0, 1.0, 0.0]
CALIB

echo "Cameras started (RS PID=$RS_PID, USB PID=$USB_PID)"
wait
