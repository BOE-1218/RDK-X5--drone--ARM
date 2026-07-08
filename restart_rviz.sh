#!/bin/bash
# 重启 rviz2 加载新配置
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
export DISPLAY=:99

# 杀旧 rviz2
for pid in $(pgrep -x rviz2); do
  kill -9 "$pid" 2>/dev/null
done
sleep 1

# 启动新 rviz2
nohup rviz2 -d /tmp/pointcloud.rviz > /tmp/rviz2.log 2>&1 &
RVIZ_PID=$!
echo "rviz2 PID: $RVIZ_PID"
sleep 4
echo "=== rviz2 running ==="
pgrep -af rviz2 | head -3
echo "=== rviz2 log (last 10) ==="
tail -10 /tmp/rviz2.log

