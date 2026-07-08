#!/bin/bash
pids=$(ps -ef | grep 'octomap_server' | grep -v grep | awk '{print $2}')
for p in $pids; do kill -9 $p 2>/dev/null; done
sleep 2
nohup bash /tmp/start_octomap.sh > /tmp/octomap.log 2>&1 &
echo "octomap restarted"
sleep 15
echo "=== octomap.log ==="
tail -15 /tmp/octomap.log
