#!/bin/bash
# 发送目标点并监控 EgoPlanner 路径规划
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

echo "=== Current odom ==="
timeout 3 ros2 topic echo /odom --once 2>&1 | grep -A4 'position:' | head -5

echo "=== Sending goal (2.0, 0.0, 0.5) ==="
ros2 topic pub --once /move_base_simple/goal geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: 'odom'}, pose: {position: {x: 2.0, y: 0.0, z: 0.5}, orientation: {w: 1.0}}}" 2>&1 | tail -3

echo "=== Waiting for planning (8s) ==="
sleep 8

echo "=== EgoPlanner log (last 25) ==="
tail -25 /tmp/ego_planner.log

echo "=== optimal_list (trajectory viz) ==="
timeout 4 ros2 topic echo /optimal_list --once 2>&1 | head -15

echo "=== planning/bspline ==="
timeout 4 ros2 topic echo /planning/bspline --once 2>&1 | head -15

