#!/bin/bash
# 在飞控的 NSH 上通过 mavlink console 发命令查固件信息
# PX4 支持 COMMAND_LONG MAV_CMD_DO_SET_PARAMETER 方式调用 NSH？不行
# 改用 pymavlink 直接发 SERIAL_CONTROL 把命令打到 NSH 控制台
echo '=== send ver all via SERIAL_CONTROL ==='
timeout 8 python3 << 'PYEOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
hb = m.wait_heartbeat(timeout=4)
if hb is None:
    print('NO HEARTBEAT')
    raise SystemExit(1)
print(f'connected sysid={m.target_system} compid={m.target_component}')

# 请求 SERIAL_CONTROL 通道 0 (shell)
# 先取得控制权
m.mav.serial_control_send(
    target_system=m.target_system,
    target_component=m.target_component,
    device=mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
    flags=mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
    timeout=0,
    baudrate=0,
    count=0,
    data=[]
)
time.sleep(0.2)
# 发命令
cmd = b'ver all\n'
m.mav.serial_control_send(
    target_system=m.target_system,
    target_component=m.target_component,
    device=mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
    flags=mavutil.mavlink.SERIAL_CONTROL_FLAG_EXCLUSIVE | mavutil.mavlink.SERIAL_CONTROL_FLAG_RESPOND,
    timeout=0,
    baudrate=0,
    count=len(cmd),
    data=list(cmd)
)
# 收集响应
deadline = time.time() + 4
output = b''
while time.time() < deadline:
    try:
        msg = m.recv_match(type='SERIAL_CONTROL', blocking=True, timeout=0.5)
        if msg is None:
            continue
        output += bytes(msg.data[:msg.count])
        if b'px4guid' in output.lower() or b'uri' in output.lower():
            break
    except Exception as e:
        print('recv err:', e)
        break

print('=== NSH OUTPUT ===')
print(output.decode('utf-8', errors='replace'))

# 释放控制
m.mav.serial_control_send(
    target_system=m.target_system,
    target_component=m.target_component,
    device=mavutil.mavlink.SERIAL_CONTROL_DEV_SHELL,
    flags=0,
    timeout=0,
    baudrate=0,
    count=0,
    data=[]
)
PYEOF

