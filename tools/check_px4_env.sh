#!/bin/bash
echo '=== ROS2 ==='
ros2 --version 2>&1 || echo "ROS_DISTRO=$ROS_DISTRO"
echo '=== pymavlink ==='
python3 -c 'import pymavlink; print(pymavlink.__version__)' 2>&1
echo '=== serial perm ==='
ls -l /dev/ttyUSB0
id
echo '=== ros2 ws ==='
ls ~/ros2_working_place/src/ 2>/dev/null | head -20
echo '=== mavproxy heartbeat test ==='
timeout 8 python3 -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
print('waiting heartbeat...')
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT (timeout)')
else:
    print('OK type=', hb.get_type(), 'sysid=', hb.get_srcSystem(), 'compid=', hb.get_srcComponent(), 'base_mode=', hb.base_mode, 'custom_mode=', hb.custom_mode)
"

