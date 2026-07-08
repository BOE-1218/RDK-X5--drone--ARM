#!/bin/bash
timeout 25 python3 -u << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected sysid={m.target_system} compid={m.target_component}')

# 释放再占用 shell
m.mav.serial_control_send(
    m.target_system, m.target_component,
    mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL, 0, 0, 0,
    [0]*70
)
time.sleep(0.3)

def send_cmd(cmd_str):
    # 把命令编码, 末尾加换行, 补齐到 70 字节
    payload = (cmd_str + '\n').encode('latin-1')
    if len(payload) > 70:
        payload = payload[:70]
    data = list(payload) + [0]*(70-len(payload))
    m.mav.serial_control_send(
        m.target_system, m.target_component,
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
        0, len(payload), data
    )

def collect(timeout_sec=3):
    deadline = time.time() + timeout_sec
    out = bytearray()
    while time.time() < deadline:
        msg = m.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=0.3)
        if msg is None:
            continue
        d = bytes(msg.data)
        out += d[:msg.count]
    return bytes(out)

# 先丢掉 prompt 历史输出
send_cmd('')
collect(0.5)

cmds = [
    'param show MAV_1*',
    'param show SER_TEL2*',
    'param show MAV_0*',
    'mavlink status',
]
for cmd in cmds:
    print(f'\n--- {cmd} ---')
    send_cmd(cmd)
    out = collect(3)
    print(out.decode(errors='replace'))

# 释放
m.mav.serial_control_send(
    m.target_system, m.target_component,
    mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL, 0, 0, 0, [0]*70
)
PYEOF
echo "exit=$?"

