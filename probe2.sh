#!/bin/bash
timeout 15 python3 -u << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected: from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  type={hb.type} autopilot={hb.autopilot} base_mode={hb.base_mode} custom_mode={hb.custom_mode}')

# 拉关键参数
print('\n--- request params ---')
params_to_read = [b'SYS_AUTOSTART', b'MAV_TYPE', b'MAV_0_MODE', b'MAV_0_CONFIG',
                  b'SYS_BOARD', b'SYS_HW_VER', b'SYS_MC_EST_GROUP', b'COM_OBS_AVOID']
for name in params_to_read:
    try:
        m.mav.param_request_read_send(m.target_system, m.target_component, name, -1)
    except Exception as e:
        print(f'  send {name}: err {e}'); continue
    msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
    if msg is None:
        print(f'  {name.decode()}: NO REPLY (timeout)')
    else:
        v = msg.param_value
        # 整数参数的话显示成整数
        if abs(v - round(v)) < 0.001:
            v = int(round(v))
        print(f'  {msg.param_id.decode().strip(chr(0))}: {v}')

# 看飞控自发会发哪些消息 (5 秒)
print('\n--- listen 5 sec ---')
deadline = time.time() + 5
counts = {}
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    counts[t] = counts.get(t, 0) + 1
for t, c in sorted(counts.items(), key=lambda x: -x[1])[:15]:
    print(f'  {t}: {c}')

PYEOF
echo "exit=$?"

