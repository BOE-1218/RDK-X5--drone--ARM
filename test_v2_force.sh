#!/bin/bash
echo '=== test: mavlink2=True parameter ==='
timeout 12 python3 -u -c "
from pymavlink import mavutil
import time

# 方法1: mavlink2 参数强制 v2
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common', mavlink2=True)
hb = m.wait_heartbeat(timeout=5)
print('hb:', hb is not None)
print('mavlink20():', m.mavlink20())
print('mavlink10():', m.mavlink10())

# 收两个心跳确认
for _ in range(2):
    hb = m.recv_match(type='HEARTBEAT', blocking=True, timeout=2)
    if hb:
        print(f'hb mavlink_version={hb.mavlink_version}')

# 试发 disarm 命令
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print('disarm ack:', ack)

# 试参数请求
m.mav.param_request_read_send(m.target_system, m.target_component, b'SYS_AUTOSTART', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
print('SYS_AUTOSTART:', msg)
"

