#!/bin/bash
# TF 静态变换: map -> odom (单位变换)
# depth_odom.py 现在发布 body 坐标系 (ROS 标准: x前, y左, z上) 的 odom
# map 与 odom 方向一致, 仅需单位变换
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

# map -> odom (单位变换)
ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom &

echo "TF publishers started"
wait
