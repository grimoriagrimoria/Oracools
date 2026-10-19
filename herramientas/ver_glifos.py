# Se corre EN la placa: imprime cada glifo como arte ASCII (sin tocar la pantalla).
import framebuf
from glifos import GLIFOS, W, H

buf = bytearray(W * H // 8)
fb = framebuf.FrameBuffer(buf, W, H, framebuf.MONO_VLSB)
for nombre, f in GLIFOS.items():
    if "SOLO" in globals() and nombre not in SOLO:
        continue
    fb.fill(0)
    f(fb, 2000)
    print("==", nombre)
    for y in range(H):
        print("".join("#" if fb.pixel(x, y) else "." for x in range(W)))
