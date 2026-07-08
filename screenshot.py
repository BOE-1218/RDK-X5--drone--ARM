import subprocess
import os

try:
    from PIL import Image
    import numpy as np
    # Use xwd to capture and convert
    subprocess.run(['xwd', '-root', '-display', ':99', '-out', '/tmp/screen.xwd'], check=True)
    subprocess.run(['convert', '/tmp/screen.xwd', '/tmp/screen.png'], check=True)
    print("Screenshot saved to /tmp/screen.png")
except Exception as e:
    print(f"Error: {e}")
    # Fallback: use import command from ImageMagick
    try:
        subprocess.run(['import', '-display', ':99', '-window', 'root', '/tmp/screen.png'], check=True)
        print("Screenshot saved to /tmp/screen.png")
    except Exception as e2:
        print(f"Fallback error: {e2}")
