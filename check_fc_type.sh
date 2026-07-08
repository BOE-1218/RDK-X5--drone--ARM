#!/bin/bash
echo '=== HEARTBEAT detail ==='
timeout 5 python3 -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
hb = m.wait_heartbeat(timeout=4)
if hb is None:
    print('NO HEARTBEAT')
else:
    print('type=', hb.type)
    print('autopilot=', hb.autopilot, '(0=GENERIC, 2=SLUGS, 3=ARDUPILOTMEGA, 5=PX4, 12=AUTOPILOT_INVALID)')
    print('base_mode=', hb.base_mode)
    print('custom_mode=', hb.custom_mode)
    print('system_status=', hb.system_status)
    print('mavlink_version=', hb.mavlink_version)
"
echo '=== AUTOPILOT_VERSION request ==='
timeout 6 python3 -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600)
m.wait_heartbeat(timeout=4)
m.mav.autopilot_version_request_send(m.target_system, m.target_component)
msg = m.recv_match(type='AUTOPILOT_VERSION', blocking=True, timeout=3)
if msg is None:
    print('NO AUTOPILOT_VERSION reply')
else:
    print('flight_sw_version=', msg.flight_sw_version)
    print('middleware_sw_version=', msg.middleware_sw_version)
    print('board_version=', msg.board_version)
    print('vendor_id=', msg.vendor_id)
    print('product_id=', msg.product_id)
    uid = msg.uid
    print('uid=', uid)
    hw = bytes(msg.flight_custom_version).decode('utf-8', errors='replace') if msg.flight_custom_version else ''
    print('flight_custom_version=', hw)
"

