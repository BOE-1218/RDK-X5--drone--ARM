#!/bin/bash
set -x
pkill -9 -f px4_node
sleep 1
pkill -9 -f 'ros2 launch aerial'
sleep 2
echo "=== remaining processes ==="
ps -ef | grep -E 'px4_node|aerial' | grep -v grep
echo "=== ttyUSB devices ==="
ls /dev/ttyUSB* 2>&1
echo "=== fuser ==="
fuser /dev/ttyUSB1 2>&1
