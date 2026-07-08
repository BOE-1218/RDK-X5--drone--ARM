#!/bin/bash
# 杀掉旧进程并重启
pids=$(ps -ef | grep 'python3 /tmp/depth' | grep -v grep | awk '{print $2}')
for p in $pids; do kill -9 $p 2>/dev/null; done
pids2=$(ps -ef | grep 'octomap_server' | grep -v grep | awk '{print $2}')
for p in $pids2; do kill -9 $p 2>/dev/null; done
sleep 2

# 重启 depth_odom
nohup bash /tmp/start_depth_odom.sh > /tmp/depth_odom.log 2>&1 &
echo "depth_odom restarted"
sleep 4

# 重启 octomap
nohup bash /tmp/start_octomap.sh > /tmp/octomap.log 2>&1 &
echo "octomap restarted"
sleep 15

echo "=== depth_odom.log ==="
tail -10 /tmp/depth_odom.log
echo "=== octomap.log ==="
tail -10 /tmp/octomap.log
