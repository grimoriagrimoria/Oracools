# Se corre EN la placa: arranca al Oracool (opcionalmente con dirección aleatoria) y
# cuenta qué pasa con el Bluetooth durante 40 s.
import time
import bluetooth

if globals().get("ALEATORIA"):
    b = bluetooth.BLE()
    b.active(True)
    b.config(addr_mode=1)  # dirección aleatoria estática: para la PC es "otro" aparato
    print("direccion:", b.config("mac"))

from oracool import Oracool

o = Oracool()
e = o.enlace
print("servicios:", e._h_escucha, e._h_voz, e._h_lienzo)
orig = e._irq
def espia(evento, datos):
    print("irq", evento)
    orig(evento, datos)
e._ble.irq(espia)
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < 40_000:
    o.paso()
    time.sleep_ms(40)
print("fin; conectado:", e.conectado())
