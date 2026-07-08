#!/bin/bash
echo '=== 持续发数据 30 秒, 用万用表测 CH340 TX 引脚电压 ==='
echo '预期: 静态约 3.3V, 发数据时电压会跳变 (平均降到 1.5-2V 左右)'
echo '如果一直 0V -> CH340 TX 引脚没输出, 模块坏了'
echo '如果一直 3.3V 不动 -> CH340 TX 没在发, 或者 USB 数据没到 TX'
echo '如果在 1-3V 之间跳动 -> CH340 TX 正常, 问题在飞控侧接线'
echo
echo '开始发送 (30秒)...'
python3 -u -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=0)
ser.reset_input_buffer()
start = time.time()
total = 0
while time.time() - start < 30:
    n = ser.write(b'\xfe\x09\x00\xff\xbe\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00' * 4)
    total += n
    ser.flush()
    time.sleep(0.05)
print(f'wrote {total} bytes in 30 sec')
ser.close()
"
echo '发送结束'

