#!/bin/bash
echo '=== simple heartbeat recheck ==='
fuser /dev/ttyUSB0 2>/dev/null && echo "device busy with PID(s) above" || echo "device free"
echo '--- try heartbeat ---'
timeout 6 python3 -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, force_msg_received=True)
hb = m.wait_heartbeat(timeout=5)
print('hb =', hb)
"
echo "exit=$?"

