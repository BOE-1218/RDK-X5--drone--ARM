#!/bin/bash
# 重启 depth_odom 和 TF 发布器
# 脚本以文件方式执行, SSH 命令行不含搜索模式, 避免 pkill 误杀

# 杀旧 depth_odom.py (按 PID 杀, 不用 pkill -f)
for pid in $(pgrep -f '/tmp/depth_odom.py'); do
  [ "$pid" = "$$" ] && continue
  kill -9 "$pid" 2>/dev/null
done

# 杀旧 static_transform_publisher
for pid in $(pgrep -f 'static_transform_publisher'); do
  [ "$pid" = "$$" ] && continue
  kill -9 "$pid" 2>/dev/null
done

sleep 1

# 启动新 TF (map -> odom 单位变换)
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
nohup ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom > /tmp/tf.log 2>&1 &
TF_PID=$!

# 启动新 depth_odom.py
nohup python3 /tmp/depth_odom.py > /tmp/depth_odom.log 2>&1 &
DVO_PID=$!

sleep 3

echo "=== Restarted ==="
echo "TF PID: $TF_PID"
echo "DVO PID: $DVO_PID"
echo "=== Processes ==="
pgrep -af 'depth_odom|static_transform' | head -5
echo "=== depth_odom log (last 15) ==="
tail -15 /tmp/depth_odom.log

