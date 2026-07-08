#!/bin/bash
# 启动 EgoPlanner 并检查 occupancy grid
. /opt/ros/humble/setup.bash
. /root/ego_ws/install/setup.bash
export ROS_LOCALHOST=1

# 杀旧 ego_planner
for pid in $(pgrep -f 'ego_planner_node'); do
  [ "$pid" = "$$" ] && continue
  kill -9 "$pid" 2>/dev/null
done
sleep 1

# 启动 EgoPlanner
nohup bash /tmp/start_ego.sh > /tmp/ego_planner.log 2>&1 &
EGO_PID=$!
echo "EgoPlanner PID: $EGO_PID"

# 等待 EgoPlanner 初始化和接收数据
sleep 12

echo "=== EgoPlanner log (last 30) ==="
tail -30 /tmp/ego_planner.log

echo "=== occupancy grid check ==="
timeout 5 ros2 topic echo /grid_map/occupancy --once 2>&1 | head -15

echo "=== topic list ==="
ros2 topic list | grep -E 'grid_map|occupancy'

