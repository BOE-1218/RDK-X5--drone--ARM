#!/bin/bash
echo '=== 深度诊断: 命令到底是不是被丢弃 ==='
timeout 20 python3 -u -c "
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
print(f'heartbeat from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  target_system={m.target_system} target_component={m.target_component}')

# 收所有消息看 STATUSTEXT 是否有报错
print('\n--- 发送 disarm 命令并监听所有响应 3秒 ---')
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
deadline = time.time() + 3
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    if t in ('COMMAND_ACK', 'STATUSTEXT', 'AUTOPILOT_VERSION'):
        print(f'{t}: {msg.to_dict()}')
    elif t == 'HEARTBEAT':
        print(f'HB: armed={bool(msg.base_mode & 128)} mode={msg.custom_mode}')
print('--- end disarm test ---')

# 试试 target_component=0 (广播)
print('\n--- 用 target_component=0 再试 ---')
m.mav.command_long_send(
    1, 0,
    mavutil.mavlink.MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES,
    0, 1.0, 0, 0, 0, 0, 0, 0
)
deadline = time.time() + 3
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    if t in ('COMMAND_ACK', 'STATUSTEXT', 'AUTOPILOT_VERSION'):
        print(f'{t}: {msg.to_dict()}')
print('--- end broadcast test ---')

# 参数请求用 request_list
print('\n--- param_request_list (要全部) ---')
m.mav.param_request_list_send(1, 1)
deadline = time.time() + 3
cnt = 0
while time.time() < deadline:
    msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=0.5)
    if msg is None:
        continue
    cnt += 1
    if cnt <= 3:
        print(f'  param {cnt}: {msg.param_id.decode(errors=\"replace\").strip(chr(0))} = {msg.param_value}')
print(f'total params received: {cnt}')
"

