#!/bin/bash
# 在地瓜派真实桌面 :0 上启动 rviz2 (借用 sunrise 用户的 X 授权)
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1
export DISPLAY=:0
export XAUTHORITY=/home/sunrise/.Xauthority

# 确保没有旧 rviz2
for pid in $(pgrep -x rviz2); do
  kill -9 "$pid" 2>/dev/null
done
sleep 1

# 在真实桌面启动 rviz2
nohup rviz2 -d /tmp/pointcloud.rviz > /tmp/rviz2.log 2>&1 &
RVIZ_PID=$!
echo "rviz2 PID: $RVIZ_PID (DISPLAY=:0, XAUTHORITY=/home/sunrise/.Xauthority)"
sleep 5
echo "=== rviz2 running ==="
pgrep -af rviz2 | head -3
echo "=== rviz2 log ==="
tail -15 /tmp/rviz2.log

