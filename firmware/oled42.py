# Driver mínimo para la OLED 0.42" (SSD1306, 72x40) del ESP32-C3
import framebuf
from machine import SoftI2C, Pin

W, H = 72, 40
X_OFF = 28  # el panel de 72 columnas vive en las columnas 28..99 del SSD1306


class OLED(framebuf.FrameBuffer):
    def __init__(self, sda=5, scl=6, addr=0x3C):
        self.i2c = SoftI2C(sda=Pin(sda), scl=Pin(scl), freq=400000)
        self.addr = addr
        self.buf = bytearray(W * H // 8)
        super().__init__(self.buf, W, H, framebuf.MONO_VLSB)
        for c in (0xAE, 0xD5, 0x80, 0xA8, H - 1, 0xD3, 0x00, 0x40,
                  0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x12,
                  0x81, 0xCF, 0xD9, 0xF1, 0xDB, 0x40, 0xAD, 0x30,
                  0xA4, 0xA6, 0xAF):
            self.cmd(c)
        self.fill(0)
        self.show()

    def cmd(self, c):
        self.i2c.writeto(self.addr, bytes((0x00, c)))

    def contrast(self, v):
        self.cmd(0x81)
        self.cmd(v)

    def invert(self, on):
        self.cmd(0xA7 if on else 0xA6)

    def show(self):
        for c in (0x21, X_OFF, X_OFF + W - 1, 0x22, 0, H // 8 - 1):
            self.cmd(c)
        self.i2c.writeto(self.addr, b"\x40" + self.buf)
