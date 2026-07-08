#!/bin/bash
source /opt/ros/humble/setup.bash
exec ros2 run realsense2_camera realsense2_camera_node --ros-args --params-file /tmp/camera_params.yaml
