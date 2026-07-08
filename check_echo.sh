#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== ColorPoints Echo ==="
timeout 5 ros2 topic echo /camera/depth/color_points --once 2>&1 | head -10
