#!/bin/bash
. /opt/ros/humble/setup.bash
echo "=== Installed ROS 2 Packages ==="
ros2 pkg list 2>/dev/null | grep -E "octomap|rtabmap|vins|ego|planner|realsense|v4l2|depth_image|cv_bridge|pcl|tf2|nav2|mpc|mavros"
echo "=== Build Tools ==="
which colcon
which cmake
dpkg -l | grep -E "libarmadillo|libpcl-dev|libeigen3-dev|libsuitesparse" | awk '{print $2, $3}'
echo "=== Architecture ==="
uname -m
echo "=== Memory ==="
free -h | head -2
echo "=== Disk ==="
df -h / | tail -1
echo "=== Existing Workspaces ==="
ls -la /home/*/ros2_ws/src/ 2>/dev/null || echo "no ros2_ws"
ls -la /root/ros2_ws/src/ 2>/dev/null || echo "no root ros2_ws"
