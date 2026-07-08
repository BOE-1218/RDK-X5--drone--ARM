#!/bin/bash
echo '=== 持续发数据 60 秒, 你看 mavlink status 的 rx 变化 ==='
echo '在飞控 NSH 里执行: mavlink status'
echo '看 instance #0 的 rx 字段'
echo
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0)
ser.reset_input_buffer()
start = time.time()
total = 0
while time.time() - start < 60:
    n = ser.write(b'\xfe\x09\x00\xff\xbe\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' * 4)
    total += n
    ser.flush()
    time.sleep(0.05)
print(f'wrote {total} bytes in 60 sec')
ser.close()
"
echo '发送结束'

