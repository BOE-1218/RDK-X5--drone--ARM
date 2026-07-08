#!/bin/bash
echo '=== 测试1: 强制 MAVLink1 模式发送 ==='
timeout 15 python3 -u -c "
from pymavlink import mavutil
import time

# force_msg_received=False 让 pymavlink 不根据心跳自动切 v2
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
print(f'hb mavlink_version={hb.mavlink_version}')
print(f'mavlink10={m.mavlink10()} mavlink20={m.mavlink20()}')

# 关键: 强制 v1 发送
m.force_mavlink1 = True
print(f'force_mavlink1 set to True')
print(f'now mavlink10={m.mavlink10()} mavlink20={m.mavlink20()}')

# 试参数请求
m.mav.param_request_read_send(1, 1, b'SYS_AUTOSTART', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
print(f'SYS_AUTOSTART (v1): {msg}')

m.mav.param_request_read_send(1, 1, b'MAV_TYPE', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
print(f'MAV_TYPE (v1): {msg}')

# 命令
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
print(f'disarm ack (v1): {ack}')
"

echo
echo '=== 测试2: 用 source_system=255 (GCS 标识) ==='
timeout 12 python3 -u -c "
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common', source_system=255, source_component=1)
hb = m.wait_heartbeat(timeout=5)
print(f'connected, source_system={m.source_system} source_component={m.source_component}')
print(f'target_system={m.target_system} target_component={m.target_component}')

# 显式重设 target
m.target_system = 1
m.target_component = 1

# 试命令
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
print(f'disarm ack (source=255): {ack}')

# 试参数
m.mav.param_request_read_send(1, 1, b'MAV_TYPE', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
print(f'MAV_TYPE (source=255): {msg}')
"

