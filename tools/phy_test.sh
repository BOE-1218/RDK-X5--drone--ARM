#!/bin/bash
echo '=== 发命令时同步观察飞控 rx 统计变化 ==='
echo '思路: 发送前不查询, 发送命令后立即查 mavlink status, 但需要 NSH shell'
echo '改用直接方法: 用 stty 配置 + 写大量字节 + 看是否回环'

# 1. 验证 CH340 是不是回环设备 (TX 接到自己的 RX)
echo
echo '--- test 1: loopback test (需手动短接 TX/RX, 没短接就应无回环) ---'
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0.5)
ser.reset_input_buffer()
ser.reset_output_buffer()
test_data = b'HELLO_LOOPBACK_TEST_1234567890'
n = ser.write(test_data)
ser.flush()
time.sleep(0.2)
echo = ser.read(100)
print(f'wrote {n} bytes')
print(f'read back {len(echo)} bytes: {echo}')
if echo == test_data:
    print('LOOPBACK! TX 和 RX 在模块内部被短接了')
elif len(echo) > 0:
    print(f'部分回环, 数据: {echo.hex()}')
else:
    print('无回环 (正常, 没短接的话)')
ser.close()
"

echo
echo '--- test 2: 直接写串口看 TX 是否输出 (DTR/RTS 控制) ---'
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0.5)
# 显式拉高 RTS 让对方 (如果用流控) 接收
ser.rts = True
ser.dtr = True
print(f'RTS={ser.rts} DTR={ser.dtr} CTS={ser.cts} DSR={ser.dsr} CD={ser.cd} RI={ser.ri}')
# 这几个状态信号能反映物理连接
# 如果 CTS 一直是 False, 说明 RTS/CTS 线没接或电压不对
"

echo
echo '--- test 3: 检查 ttyUSB0 设备是否正常 ---'
ls -l /dev/ttyUSB0
echo 'driver info:'
cat /sys/class/tty/ttyUSB0/device/driver/module/description 2>/dev/null || modinfo ch341 2>/dev/null | head -5
echo '---'
dmesg | grep -i ch341 | tail -5

