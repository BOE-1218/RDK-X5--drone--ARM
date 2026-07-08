#!/bin/bash
timeout 20 python3 -u << 'PYEOF'
from pymavlink import mavutil
import time, array

# 用 common dialect, serial_control data 是 array
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected sysid={m.target_system} compid={m.target_component}')
print(f'  hb from sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')

# 占据 shell
def serial_send(data_bytes, flags=0):
    # data 必须是 70 字节
    buf = data_bytes + b'\x00' * (70 - len(data_bytes))
    m.mav.serial_control_send(
        m.target_system, m.target_component,
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        flags,
        0, 0, list(buf)
    )

def collect(timeout_sec=3):
    deadline = time.time() + timeout_sec
    out = b''
    while time.time() < deadline:
        msg = m.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=0.3)
        if msg is None:
            continue
        # msg.data 是 bytes 或 array, 取前 count 字节
        d = bytes(msg.data)
        out += d[:msg.count]
    return out

print('\n--- acquire shell exclusive ---')
serial_send(b'', flags=mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND)
time.sleep(0.5)
collect(0.5)  # 丢掉 prompt 历史输出

cmds = [
    'param show MAV_1*',
    'param show SER_TEL2*',
    'param show MAV_0*',
    'mavlink status',
]
for cmd in cmds:
    print(f'\n--- {cmd} ---')
    serial_send((cmd + '\n').encode(),
                flags=mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND)
    out = collect(3)
    print(out.decode(errors='replace'))

# 释放
serial_send(b'', flags=0)
PYEOF
echo "exit=$?"

