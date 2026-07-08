#!/bin/bash
pkill -9 -f realsense2_camera_node 2>/dev/null
pkill -9 -f 'ros2 launch' 2>/dev/null
sleep 3
nohup bash /tmp/start_cameras3.sh > /tmp/cameras.log 2>&1 &
echo "RealSense restarted, PID=$!"
sleep 10
echo "=== cameras.log ==="
tail -10 /tmp/cameras.log
echo "=== 点云发布者 ==="
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
ros2 topic info /camera/camera/depth/points 2>&1 | head -5
