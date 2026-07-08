#!/bin/bash
echo '=== full param list request ==='
timeout 20 python3 -u << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, force_msg_received=True)
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  type={hb.type} autopilot={hb.autopilot} base_mode={hb.base_mode:#x} custom_mode={hb.custom_mode:#x}')
print(f'  base_mode bits: CUSTOM={bool(hb.base_mode & 1)} TEST={bool(hb.base_mode & 2)} AUTO={bool(hb.base_mode & 4)} GUIDED={bool(hb.base_mode & 8)} STABILIZE={bool(hb.base_mode & 16)} HIL={bool(hb.base_mode & 32)} ARMED={bool(hb.base_mode & 128)}')

# 请求完整参数列表 (PARAM_REQUEST_LIST)
print('\n--- request full param list ---')
m.mav.param_request_list_send(m.target_system, m.target_component)

# 收 8 秒 PARAM_VALUE
deadline = time.time() + 8
params = {}
last_print = 0
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    if t == 'PARAM_VALUE':
        name = msg.param_id.decode(errors='replace').strip('\x00')
        v = msg.param_value
        if abs(v - round(v)) < 0.001:
            v = int(round(v))
        params[name] = v
        if len(params) % 20 == 0 and len(params) != last_print:
            print(f'  received {len(params)} params...')
            last_print = len(params)
    elif t == 'HEARTBEAT':
        pass  # 心跳不影响

print(f'\nTOTAL params received: {len(params)}')
print('\n--- key params ---')
for k in ['SYS_AUTOSTART', 'MAV_TYPE', 'MAV_0_CONFIG', 'MAV_0_MODE',
          'MAV_1_CONFIG', 'MAV_1_MODE', 'MAV_1_RATE',
          'SER_TEL2_BAUD', 'COM_RC_IN_MODE', 'COM_ARM_AUTH_METHOD',
          'COM_OFLOSS_T', 'COM_RCL_EXCEPT', 'SYS_BOARD', 'SYS_HW_VER']:
    if k in params:
        print(f'  {k}: {params[k]}')
    else:
        print(f'  {k}: <not in list>')

# 试着请求 COMMAND_ACK 看 commander 响应不
print('\n--- test command ack (DO_SET_MODE to current mode = HOLD) ---')
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
    0,
    mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED,  # 这里写错了也无妨, 测试响应
    0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print(f'ack: {ack}')

PYEOF
echo "exit=$?"

