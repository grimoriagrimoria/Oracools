# Se corre EN la placa: dibuja tres momentos de cada animación de ofrenda, lado a lado.
# (cada dos renglones, para que quepa)
import framebuf
from ofrendas import ANIMACIONES
from glifos import W, H

MOMENTOS = (350, 900, 1500)
bufs = [bytearray(W * H // 8) for _ in MOMENTOS]
fbs = [framebuf.FrameBuffer(b, W, H, framebuf.MONO_VLSB) for b in bufs]
for nombre, f in ANIMACIONES.items():
    if "SOLO" in globals() and nombre not in SOLO:
        continue
    for fb, dt in zip(fbs, MOMENTOS):
        fb.fill(0)
        f(fb, dt)
    print("==", nombre, MOMENTOS)
    for y in range(0, H, 2):
        print(" | ".join("".join("#" if fb.pixel(x, y) else " " for x in range(W)) for fb in fbs).rstrip())
