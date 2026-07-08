#!/bin/bash
# 重启 depth_odom 和 octomap
pkill -9 -f depth_visual_odom 2>/dev/null
pkill -9 -f octomap_server_node 2>/dev/null
sleep 2

# 重置 depth_odom 累积位姿 (重新启动)
nohup bash /tmp/start_depth_odom.sh > /tmp/depth_odom.log 2>&1 &
echo "depth_odom started, PID=$!"
sleep 4

# 重启 octomap
nohup bash /tmp/start_octomap.sh > /tmp/octomap.log 2>&1 &
echo "octomap started, PID=$!"
sleep 5

echo "=== depth_odom.log ==="
tail -8 /tmp/depth_odom.log
echo "=== octomap.log ==="
tail -8 /tmp/octomap.log
echo "=== 点云话题 ==="
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
ros2 topic info /camera/depth/points 2>&1 | head -5
echo "=== 点云频率 ==="
timeout 5 ros2 topic hz /camera/depth/points 2>&1 | tail -3
