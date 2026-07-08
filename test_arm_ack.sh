#!/bin/bash
# 直接用 mavlink 测试 arm/disarm ACK 是否到达
source /opt/ros/humble/setup.bash
python3 << 'EOF'
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB1', baud=921600, dialect='common')
print('等待心跳...')
hb = m.wait_heartbeat(timeout=10)
if hb is None:
    print('心跳超时')
    exit(1)
print(f'已连接 sys={m.target_system} comp={m.target_component}')

def send_arm(disarm):
    cmd = mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM
    param = 0.0 if disarm else 1.0
    m.mav.command_long_send(
        m.target_system, m.target_component,
        cmd, 0,
        param, 0, 0, 0, 0, 0, 0
    )
    print(f'已发送 {"disarm" if disarm else "arm"} 命令, 等待 ACK (3s)...')
    start = time.time()
    while time.time() - start < 3.0:
        msg = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=0.5)
        if msg is not None:
            print(f'  收到 ACK: command={msg.command} result={msg.result}')
            return
    print('  3 秒内无 ACK')

print('\n=== 测试 1: disarm (当前已 disarm) ===')
send_arm(disarm=True)

print('\n=== 测试 2: arm ===')
send_arm(disarm=False)

time.sleep(1)
print('\n=== 测试 3: 立即 disarm ===')
send_arm(disarm=True)

m.close()
EOF
