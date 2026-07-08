#!/usr/bin/env python3
"""生成 8x6 棋盘格标定板图片用于打印 (纯 PIL 实现).

规格:
  - 内角点: 8 x 6 (即 9 x 7 方格)
  - 每格边长: 25mm (打印时需确保 100% 比例, A4 横向)
  - 输出: checkerboard_8x6_25mm.png
"""
from PIL import Image, ImageDraw

# 棋盘格参数
COLS = 9   # 列数 (方格数 = 内角点数 + 1)
ROWS = 7   # 行数 (方格数 = 内角点数 + 1)
SQUARE_PX = 200  # 每格像素 (高分辨率)
MARGIN_PX = 200  # 边缘留白
SIZE_MM = 25  # 每格实际边长 mm

board_w = COLS * SQUARE_PX + 2 * MARGIN_PX
board_h = ROWS * SQUARE_PX + 2 * MARGIN_PX

img = Image.new("L", (board_w, board_h), 255)
draw = ImageDraw.Draw(img)

for r in range(ROWS):
    for c in range(COLS):
        if (r + c) % 2 == 0:
            x0 = MARGIN_PX + c * SQUARE_PX
            y0 = MARGIN_PX + r * SQUARE_PX
            x1 = x0 + SQUARE_PX
            y1 = y0 + SQUARE_PX
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=0)

out = "checkerboard_8x6_25mm.png"
img.save(out)
print(f"已生成: {out}")
print(f"尺寸: {board_w}x{board_h} 像素")
print(f"规格: {COLS}x{ROWS} 方格 = {COLS-1}x{ROWS-1} 内角点")
print(f"每格: {SIZE_MM}mm")
print(f"打印要求: A4 纸横向, 100% 比例, 不要缩放")
print(f"打印后需用尺子验证每格实际边长确实是 {SIZE_MM}mm")

