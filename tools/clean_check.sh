#!/bin/bash
# 清理所有旧进程
pkill -f rviz2 2>/dev/null
pkill -f rtabmap 2>/dev/null
pkill -f realsense2_camera 2>/dev/null
pkill -f v4l2_camera 2>/dev/null
pkill -f rgb_depth_fusion 2>/dev/null
pkill -f x11vnc 2>/dev/null
pkill -f Xvfb 2>/dev/null
pkill -f static_transform 2>/dev/null
pkill -f octomap 2>/dev/null
sleep 2
echo "=== Cleaned ==="
ps aux | grep -E "rviz2|rtabmap|realsense|v4l2|rgb_depth|x11vnc|Xvfb" | grep -v grep || echo "All clean"

# 确认摄像头设备
echo "=== Video Devices ==="
. /opt/ros/humble/setup.bash
for dev in /dev/video*; do
    echo "--- $dev ---"
    v4l2-ctl -d "$dev" --info 2>/dev/null | head -3 || echo "no info"
done
