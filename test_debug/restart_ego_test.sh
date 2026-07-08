#!/bin/bash
# 重启 EgoPlanner (depth_filter_mindist=0.5), 发送目标点, 检查路径规划
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1

# 杀旧 ego_planner
for pid in $(pgrep -f 'ego_planner_node'); do
  [ "$pid" = "$$" ] && continue
  kill -9 "$pid" 2>/dev/null
done
sleep 2

# 启动新 EgoPlanner
nohup bash /tmp/start_ego.sh > /tmp/ego_planner.log 2>&1 &
EGO_PID=$!
echo "EgoPlanner PID: $EGO_PID"

# 等待初始化
sleep 12

echo "=== EgoPlanner log (last 15) ==="
tail -15 /tmp/ego_planner.log

echo ""
echo "=== Drone position ==="
timeout 3 ros2 topic echo /odom --once 2>&1 | grep -A3 'position:' | head -5

echo ""
echo "=== Sending goal (1.5, 0.0, 0.0) forward ==="
ros2 topic pub --once /move_base_simple/goal geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: 'odom'}, pose: {position: {x: 1.5, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}" 2>&1 | tail -2

# 等待路径规划
sleep 8

echo ""
echo "=== EgoPlanner log after goal (last 25) ==="
tail -25 /tmp/ego_planner.log

echo ""
echo "=== planning/bspline (trajectory) ==="
timeout 4 ros2 topic echo /planning/bspline --once 2>&1 | head -10

echo ""
echo "=== optimal_list (trajectory viz) ==="
timeout 4 ros2 topic echo /optimal_list --once 2>&1 | head -10

