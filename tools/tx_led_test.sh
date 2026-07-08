#!/bin/bash
echo '=== 持续发数据 10 秒, 你看 CH340 模块的 TX LED 灯 ==='
echo '如果 TX LED 在闪 -> CH340 收到数据并输出到 TX 引脚'
echo '如果 TX LED 不闪 -> CH340 没工作'
echo
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0)
ser.reset_input_buffer()
start = time.time()
total = 0
while time.time() - start < 10:
    # 发 64 字节 MAVLink 心跳格式的填充数据
    n = ser.write(b'\xfe\x09\x00\xff\xbe\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' * 4)
    total += n
    ser.flush()
    time.sleep(0.05)
print(f'wrote {total} bytes in 10 sec')
ser.close()
"
echo
echo '现在请看飞控 NSH, 执行 mavlink status, 看 instance #0 的 rx 字段:'
echo '如果飞控 rx > 0 -> 物理层通了, 是协议层问题'
echo '如果飞控 rx = 0 -> CH340 TX 信号没到飞控 RX 引脚'

