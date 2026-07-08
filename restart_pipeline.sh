#!/bin/bash
# 重启管线: 杀掉旧进程, 启动新管线
pkill -9 -f point_cloud_xyz_node 2>/dev/null
pkill -9 -f octomap_server_node 2>/dev/null
pkill -9 -f realsense2_camera_node 2>/dev/null
pkill -9 -f 'ros2 launch' 2>/dev/null
sleep 3

# 启动 RealSense (含 pointcloud)
nohup bash /tmp/start_cameras3.sh > /tmp/cameras.log 2>&1 &
echo "RealSense started, PID=$!"
sleep 8

# 启动 OctoMap
nohup bash /tmp/start_octomap.sh > /tmp/octomap.log 2>&1 &
echo "OctoMap started, PID=$!"
sleep 3

echo "=== cameras.log ==="
tail -5 /tmp/cameras.log
echo "=== octomap.log ==="
tail -5 /tmp/octomap.log
