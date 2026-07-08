#!/bin/bash
# 通过 mavlink console 发命令查 TELEM2 配置
# 用 SERIAL_CONTROL_DEV_SHELL 通道
timeout 15 python3 -u << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected sysid={m.target_system} compid={m.target_component}')

# 取得 NSH shell 控制权
print('\n--- acquire shell ---')
m.mav.serial_control_send(
    m.target_system, m.target_component,
    mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
    mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
    0, 0, []
)
time.sleep(0.3)

# 发命令 + 换行
def send_cmd(cmd):
    data = (cmd + '\n').encode()
    m.mav.serial_control_send(
        m.target_system, m.target_component,
        mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
        mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
        0, len(data), list(data)
    )

def collect(timeout_sec=3):
    deadline = time.time() + timeout_sec
    out = b''
    while time.time() < deadline:
        msg = m.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=0.3)
        if msg is None:
            continue
        out += bytes(msg.data[:msg.count])
    return out

# 先丢掉之前可能积累的输出
collect(0.5)

print('--- send "param show MAV_1*" ---')
send_cmd('param show MAV_1*')
print(collect(3).decode(errors='replace'))

print('--- send "param show SER_TEL2*" ---')
send_cmd('param show SER_TEL2*')
print(collect(3).decode(errors='replace'))

print('--- send "param show MAV_0*" ---')
send_cmd('param show MAV_0*')
print(collect(3).decode(errors='replace'))

print('--- send "mavlink status" ---')
send_cmd('mavlink status')
print(collect(3).decode(errors='replace'))

# 释放控制权
m.mav.serial_control_send(
    m.target_system, m.target_component,
    mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL, 0, 0, 0, []
)
PYEOF
echo "exit=$?"

