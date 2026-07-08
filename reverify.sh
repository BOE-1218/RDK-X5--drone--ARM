#!/bin/bash
echo '=== 重新验证双向通信 ==='
echo
echo '--- 1. 确认串口设备 ---'
ls -l /dev/ttyUSB* 2>/dev/null
echo
echo '--- 2. 心跳 + 参数请求 + 命令 ACK ---'
timeout 20 python3 -u -c "
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT')
    raise SystemExit(1)
print(f'connected sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  type={hb.type} autopilot={hb.autopilot} base_mode={hb.base_mode} custom_mode={hb.custom_mode}')

# 显式设置 target
m.target_system = 1
m.target_component = 1

# 等一秒让链路稳定
time.sleep(1)
m.recv_match(blocking=True, timeout=1)  # 丢一个心跳

# 测参数请求
print('\n--- 参数请求 ---')
for name in [b'SYS_AUTOSTART', b'MAV_TYPE', b'MAV_1_FLOW_CTRL']:
    m.mav.param_request_read_send(1, 1, name, -1)
    msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
    if msg is None:
        print(f'  {name.decode()}: NO REPLY')
    else:
        v = msg.param_value
        if abs(v - round(v)) < 0.001:
            v = int(round(v))
        print(f'  {msg.param_id.decode().strip(chr(0))}: {v}')

# 测命令 ACK (请求 AUTOPILOT_CAPABILITIES, 不影响飞行状态)
print('\n--- 命令 ACK 测试 ---')
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES,
    0, 1.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print(f'ack: {ack}')

if ack:
    ver = m.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=3)
    if ver:
        fw = ver.flight_sw_version
        print(f'flight_sw_version: {(fw >> 24) & 0xFF}.{(fw >> 16) & 0xFF}.{(fw >> 8) & 0xFF}')
        print(f'board_version: {ver.board_version}')
        print(f'uid: {ver.uid:#x}')
"

