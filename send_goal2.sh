#!/bin/bash
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
echo "=== Drone pos ==="
timeout 3 ros2 topic echo /odom --once 2>&1 | grep -A3 'position:' | head -5
echo "=== Sending new goal (2.0, 0.5, 0.0) ==="
ros2 topic pub --once /move_base_simple/goal geometry_msgs/msg/PoseStamped "{header: {frame_id: 'odom'}, pose: {position: {x: 2.0, y: 0.5, z: 0.0}, orientation: {w: 1.0}}}" 2>&1 | tail -2
sleep 5
echo "=== EgoPlanner log (last 15) ==="
tail -15 /tmp/ego_planner.log

