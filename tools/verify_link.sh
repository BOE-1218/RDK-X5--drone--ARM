#!/bin/bash
echo '=== MAVLink 双向通信验证 ==='
timeout 25 python3 -u -c "
from pymavlink import mavutil
import time

m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
hb = m.wait_heartbeat(timeout=5)
if hb is None:
    print('NO HEARTBEAT'); raise SystemExit(1)
print(f'connected: sysid={hb.get_srcSystem()} compid={hb.get_srcComponent()}')
print(f'  type={hb.type} autopilot={hb.autopilot} base_mode={hb.base_mode} custom_mode={hb.custom_mode}')
m.target_system = 1
m.target_component = 1

# 1. 参数请求测试 (RX方向)
print('\n--- 1. 参数请求 (RX方向验证) ---')
test_params = [b'SYS_AUTOSTART', b'MAV_TYPE', b'MAV_1_CONFIG', b'MAV_1_FLOW_CTRL', b'SER_TEL2_BAUD']
for name in test_params:
    m.mav.param_request_read_send(1, 1, name, -1)
    msg = m.recv_match(type='PARAM_VALUE', blocking=True, timeout=2)
    if msg is None:
        print(f'  {name.decode()}: NO REPLY')
    else:
        v = msg.param_value
        if abs(v - round(v)) < 0.001:
            v = int(round(v))
        print(f'  {msg.param_id.decode().strip(chr(0))}: {v}')

# 2. 命令 ACK 测试 (TX方向)
print('\n--- 2. 命令 ACK 测试 (TX方向验证) ---')
# 不实际 arm, 发个无害的 prefetch command (MAV_CMD_PREFLIGHT_REVISION = 0x80)
# 改用 COMMAND_LONG MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES (520)
m.mav.command_long_send(
    1, 1,
    mavutil.mavlink.MAV_CMD_REQUEST_AUTOPILOT_CAPABILITIES,
    0, 1.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
print(f'capabilities req ack: {ack}')

# 收 AUTOPILOT_VERSION (会被上面的命令触发)
ver = m.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=3)
if ver:
    fw = ver.flight_sw_version
    mw = ver.middleware_sw_version
    print(f'flight_sw: {fw >> 8 & 0xFF}.{fw & 0xFF} ({ver.flight_custom_version})')
    print(f'middleware: {mw >> 8 & 0xFF}.{mw & 0xFF}')
    print(f'board: {ver.board_version}, vendor={ver.vendor_id:#x}, product={ver.product_id:#x}')
    print(f'uid: {ver.uid:#x}')
else:
    print('AUTOPILOT_VERSION: NO REPLY')

# 3. 收集状态消息 (心跳 + SYS_STATUS + LOCAL_POSITION_NED)
print('\n--- 3. 5秒消息流统计 ---')
deadline = time.time() + 5
counts = {}
while time.time() < deadline:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None:
        continue
    t = msg.get_type()
    counts[t] = counts.get(t, 0) + 1
for t, c in sorted(counts.items(), key=lambda x: -x[1])[:10]:
    print(f'  {t}: {c}')

print('\n=== 验证完成 ===')
"

