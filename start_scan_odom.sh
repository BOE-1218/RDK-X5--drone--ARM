#!/bin/bash
# 启动 scan_odom 和 slam_toolbox
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ROS_IP=192.168.51.252

# 停止旧进程
pkill -9 -f scan_odom 2>/dev/null
sleep 1

# 启动 scan_odom (严格静态阈值)
nohup python3 /tmp/scan_odom.py --ros-args \
  -p scan_topic:=/scan \
  -p frame_id:=camera_link \
  -p odom_frame_id:=odom \
  -p max_translation_per_frame:=0.02 \
  -p max_rotation_per_frame:=0.05 \
  -p static_frames_threshold:=1 \
  > /tmp/scan_odom.log 2>&1 < /dev/null &
SCAN_PID=$!
disown

sleep 3
echo "scan_odom PID: $SCAN_PID"
pgrep -af scan_odom | grep -v grep
tail -5 /tmp/scan_odom.log
