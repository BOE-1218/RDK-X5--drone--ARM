#!/usr/bin/env python3
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import struct
import sys

def read_pgm(path):
    with open(path, 'rb') as f:
        magic = f.readline().strip()
        if magic != b'P5':
            raise ValueError(f'Unsupported PGM magic: {magic}')
        # Skip comments
        line = f.readline()
        while line.startswith(b'#'):
            line = f.readline()
        w, h = map(int, line.split())
        maxval = int(f.readline())
        data = f.read()
    arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w)
    return arr

def read_yaml(path):
    meta = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
    return meta

pgm_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/slam_map.pgm'
yaml_path = pgm_path.replace('.pgm', '.yaml')
out_path = pgm_path.replace('.pgm', '.png')

arr = read_pgm(pgm_path)
meta = read_yaml(yaml_path)
resolution = float(meta.get('resolution', 0.05))
origin = eval(meta.get('origin', '[0, 0, 0]'))

# PGM value mapping: 0 = occupied (black), 254 = free (white), 205 = unknown (gray)
# In map_saver: occ=0.65 -> 0 (black), free=0.25 -> 254 (white), unknown -> 205
disp = np.zeros_like(arr, dtype=float)
disp[arr == 0] = 0.0      # occupied -> black
disp[arr == 254] = 1.0    # free -> white
disp[arr == 205] = 0.5    # unknown -> gray
disp[(arr != 0) & (arr != 254) & (arr != 205)] = 0.7  # other -> light gray

h, w = arr.shape
extent = [
    origin[0],
    origin[0] + w * resolution,
    origin[1],
    origin[1] + h * resolution,
]

fig, ax = plt.subplots(1, 1, figsize=(10, 8))
ax.imshow(disp, extent=extent, origin='lower', cmap='gray', vmin=0, vmax=1)

# Mark origin (robot start position roughly at map origin)
robot_x = origin[0] if origin[0] != 0 else 0
robot_y = origin[1] if origin[1] != 0 else 0
# Robot is typically at (0,0) in map frame, but map origin may be offset
# Draw robot at (0, 0) map frame
circle = Circle((0, 0), 0.15, color='red', fill=True, label='Robot (origin)')
ax.add_patch(circle)
ax.plot(0, 0, 'r^', markersize=10, label='Robot pose')

ax.set_title(f'SLAM Map  ({w}x{h} @ {resolution}m/pix, origin=({origin[0]:.2f},{origin[1]:.2f}))', fontsize=12)
ax.set_xlabel('X (meters)')
ax.set_ylabel('Y (meters)')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

# Add color legend text
ax.text(0.02, 0.02, 'Black=occupied  White=free  Gray=unknown',
        transform=ax.transAxes, fontsize=9,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig(out_path, dpi=120, bbox_inches='tight')
print(f'Saved: {out_path}')
print(f'Map size: {w} x {h} pixels = {w*resolution:.2f} x {h*resolution:.2f} meters')
print(f'Origin: ({origin[0]:.3f}, {origin[1]:.3f})')
