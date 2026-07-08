#!/bin/bash
echo '=== query PX4 firmware via MAVLink ==='
timeout 12 python3 << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
hb = m.wait_heartbeat(timeout=4)
if hb is None:
    print('NO HEARTBEAT')
    raise SystemExit(1)
print(f'connected: target_system={m.target_system} target_component={m.target_component}')
print(f'heartbeat from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  type={hb.type} autopilot={hb.autopilot} base_mode={hb.base_mode} custom_mode={hb.custom_mode}')

# 1. 尝试 COMMAND_LONG MAV_CMD_PREFLIGHT_REVISION (命令 0x80 = 128)
print('\n--- try MAV_CMD_PREFLIGHT_REVISION ---')
m.mav.command_long_send(
    m.target_system, m.target_component,
    128,  # MAV_CMD_PREFLIGHT_REVISION
    0,
    0, 0, 0, 0, 0, 0, 0
)
msg = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
print('ack:', msg)

# 2. 拉取 PARAM_VALUE 看几个关键参数 (SYS_AUTOSTART, SYS_MC_EST_GROUP, MAV_TYPE)
print('\n--- request some params ---')
for name in [b'SYS_AUTOSTART', b'MAV_TYPE', b'SYS_BOARD', b'SYS_HW_VER']:
    m.mav.param_request_read_send(m.target_system, m.target_component, name, -1)
    msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
    if msg is None:
        print(f'  {name.decode()}: NO REPLY')
    else:
        print(f'  {msg.param_id.decode().strip(chr(0))}: {msg.param_value}')

# 3. 看飞控自发会发哪些消息 (统计 5 秒)
print('\n--- listen messages for 5 sec ---')
deadline = time.time() + 5
counts = {}
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    counts[t] = counts.get(t, 0) + 1
for t, c in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}')

PYEOF

