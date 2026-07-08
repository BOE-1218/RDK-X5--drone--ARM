#!/bin/bash
echo '=== test 1: stty 配置串口 + 直接写字节看 RX 灯反应 ==='
stty -F /dev/ttyUSB0 921600 raw -echo -echoe -echok -echoctl -echoke
echo 'serial config:'
stty -F /dev/ttyUSB0 -a | head -5

echo '=== test 2: write a byte, check write succeeded ==='
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0.5)
print('port opened:', ser.name, 'baud:', ser.baudrate)
n = ser.write(b'\xfe\x09\x00\xff\xff\x00\x00\x00\x00\x00\x00\x00')
print(f'wrote {n} bytes (raw MAVLink header)')
ser.flush()
time.sleep(0.3)
# 读飞控响应
ser.timeout = 1.0
data = ser.read(256)
print(f'read {len(data)} bytes back')
print('first 32 bytes hex:', data[:32].hex())
ser.close()
"

echo
echo '=== test 3: pymavlink force MAVLink 1 ==='
timeout 8 python3 -u -c "
from pymavlink import mavutil, mavlink
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common', force_msg_received=True)
m.wait_heartbeat(timeout=4)
print('hb source protocol:', m.mavlink10() and 'MAVLink1' or 'MAVLink2')
# 强制用 MAVLink 1 发命令
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
import time
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
print('arm/disarm ack (MAVLink1):', ack)
"

echo
echo '=== test 4: pymavlink force MAVLink 2 (default) ==='
timeout 8 python3 -u -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=921600, dialect='common')
m.wait_heartbeat(timeout=4)
print('mav version:', m.mavlink20() and 2 or 1)
# 让 pymavlink 自动选
m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
    0, 0.0, 0, 0, 0, 0, 0, 0
)
ack = m.recv_match(type='COMMAND_ACK', blocking=True, timeout=2)
print('arm/disarm ack (default):', ack)
"

echo
echo '=== test 5: try 57600 baud ==='
timeout 8 python3 -u -c "
from pymavlink import mavutil
m = mavutil.mavlink_connection('/dev/ttyUSB0', baud=57600, dialect='common')
hb = m.wait_heartbeat(timeout=4)
print('hb at 57600:', hb)
"

