#!/bin/bash
echo '=== test: set target_component=1 explicitly ==='
timeout 12 python3 -u -c "
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
print(f'heartbeat from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'before: target_system={m.target_system} target_component={m.target_component}')

# 显式设置目标 component 为 1 (飞控 component)
m.target_system = 1
m.target_component = 1
print(f'after: target_system={m.target_system} target_component={m.target_component}')

# 收心跳确认协议
time.sleep(0.5)
m.recv_match(blocking=True, timeout=0.5)

# 试发参数请求
m.mav.param_request_read_send(1, 1, b'SYS_AUTOSTART', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
print('SYS_AUTOSTART:', msg)

m.mav.param_request_read_send(1, 1, b'MAV_TYPE', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
print('MAV_TYPE:', msg)

# 试 disarm 命令
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print('disarm ack:', ack)

# 试 MAV_CMD_PREFLIGHT_REVISION 拿固件版本
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_PREFLIGHT_REVISION,
    0, 0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print('revision ack:', ack)
"

