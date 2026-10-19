# Se corre EN la placa (mpremote run): dibuja cada glifo y prueba los comandos.
import time
from oracool import Oracool, _envolver
from glifos import GLIFOS

o = Oracool()
print("nombre:", o.nombre)
for cara in list(GLIFOS) + ["habla", "reposo"]:
    o.comando("CARA:" + cara)
    t0 = time.ticks_ms()
    for _ in range(25):
        o.paso()
    print(cara, "ok", time.ticks_diff(time.ticks_ms(), t0) // 25, "ms/cuadro")
print(_envolver("¿De dónde venimos? ¿Quiénes somos? ¿A dónde vamos?"))
o.comando("TXT:¿De dónde venimos? ¿Quiénes somos? ¿A dónde vamos?")
for _ in range(20):
    o.paso()
o.comando("BRILLO:60")
o.comando("INV:1")
o.comando("INV:0")
o.comando("BRILLO:207")
o.comando("NADA")
o.comando("CARA:rostro")
o.paso()
o.comando("CARA:reposo")
vistos = set()
for _ in range(6):
    o._al_tocar()  # el toque salta al siguiente glifo
    for _ in range(8):
        o.paso()
    vistos.add(o._desfile[0])
print("en reposo desfilaron:", sorted(vistos))
assert len(vistos) >= 5
print("todo bien")
