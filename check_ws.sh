#!/bin/bash
echo '=== sunrise ros2_ws ==='
ls /home/sunrise/ros2_ws/ 2>/dev/null
echo '--- src ---'
ls /home/sunrise/ros2_ws/src/ 2>/dev/null
echo '--- install ---'
ls /home/sunrise/ros2_ws/install/ 2>/dev/null
echo '=== can SSH sunrise? ==='
whoami
echo '=== check sunrise ssh ==='
ls /home/sunrise/.ssh/ 2>/dev/null
cat /home/sunrise/.ssh/authorized_keys 2>/dev/null | head -2
echo '=== PX4 zip on remote? ==='
find / -name 'PX4*' -type f 2>/dev/null | head -5
echo '=== pymavlink location ==='
python3 -c "import pymavlink; print(pymavlink.__file__)"
pip3 show pymavlink 2>/dev/null | head -5

