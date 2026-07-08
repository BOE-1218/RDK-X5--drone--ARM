#!/bin/bash
echo '=== test: force MAVLink 2 send ==='
timeout 10 python3 -u -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=4)
print('hb:', hb)
print('mavlink10():', m.mavlink10(), 'mavlink20():', m.mavlink20())
# 强制切到 MAVLink 2
m.want_lnk_command_event_enable = True
m.force_mavlink1 = False
# pymavlink 在收到 MAVLink2 心跳后会自动切到 v2 发送, 但有时需要显式触发
# 直接发 COMMAND_LONG, 看 ack
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
import time
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print('ack (disarm attempt):', ack)
"

echo
echo '=== test: try param read after heartbeat ==='
timeout 15 python3 -u -c "
from pymavlink import mavutil
import time
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
m.wait_heartbeat(timeout=4)
# 等几秒让协议握手稳定
time.sleep(1)
# 再收一个心跳确认 v2 模式
for _ in range(3):
    hb = m.recv_match(type='HEARTBEAT', blocking=True, timeout=2)
    if hb:
        print(f'hb: mavlink_version={hb.mavlink_version}')
        break
# 现在发参数请求
m.mav.param_request_read_send(m.target_system, m.target_component, b'SYS_AUTOSTART', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
print('SYS_AUTOSTART:', msg)
# 试一个常见的参数
m.mav.param_request_read_send(m.target_system, m.target_component, b'MAV_TYPE', -1)
msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=3)
print('MAV_TYPE:', msg)
"

