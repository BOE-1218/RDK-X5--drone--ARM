#!/bin/bash
# 启动 Xvfb + x11vnc + rviz2
. /opt/ros/humble/setup.bash
export ROS_LOCALHOST=1

# 清理旧的 VNC 进程
pkill -9 -f Xvfb 2>/dev/null
pkill -9 -f x11vnc 2>/dev/null
pkill -9 -f rviz2 2>/dev/null
sleep 1

# 启动 Xvfb (虚拟显示)
Xvfb :99 -screen 0 1280x720x24 &
sleep 2

# 启动 x11vnc
x11vnc -display :99 -forever -shared -rfbport 5900 -nopw -bg -o /tmp/x11vnc.log
sleep 1

# 启动 rviz2
export DISPLAY=:99
export QT_QPA_PLATFORM=xcb
nohup rviz2 -d /tmp/pointcloud.rviz > /tmp/rviz2.log 2>&1 &
sleep 5

echo "=== VNC started on port 5900 ==="
echo "=== rviz2.log ==="
tail -10 /tmp/rviz2.log
