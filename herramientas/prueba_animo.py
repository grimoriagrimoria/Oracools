# Se corre EN la placa: prueba el ánima con tiempo acelerado (no toca el animo.json de verdad).
import os
import time
from animo import Animo

ARCH = "prueba_animo.json"
try:
    os.remove(ARCH)
except OSError:
    pass

a = Animo(ARCH)
print("nace:", a.reporte(), a.reporte_edad())
assert a.animo() == "S"

a.pasar(5 * 3600)                       # 5 horas a solas
print("tras 5 h:", a.reporte())
assert round(a.tierra) == 45 and round(a.chispa) == 40

for _ in range(3):
    a.ofrendar("barro")                 # sólo tierra: se desequilibra
print("mucho barro:", a.reporte())
assert a.animo() == "T"

for _ in range(3):
    a.ofrendar("chispa")
print("y chispa:", a.reporte())
assert a.animo() == "R"

a.pasar(40 * 3600)                      # casi dos días sin nadie
print("abandonado:", a.reporte())
assert a.animo() == "P"
a.ofrendar("abrazo")                    # un abrazo lo saca de la piedra
print("abrazo:", a.reporte())
assert a.animo() == "H"

# memoria y ausencias: guarda con hora real, "se apaga" 10 horas y vuelve
a.poner_hora(1_800_000_000)
t0, c0 = a.tierra, a.chispa
b = Animo(ARCH)
assert round(b.tierra) == round(t0)
b.poner_hora(1_800_000_000 + 10 * 3600 + time.ticks_ms() // 1000)
print("tras 10 h apagado:", b.reporte(), "| antes", round(t0), round(c0))
assert abs(b.tierra - max(0, t0 - 30)) < 1.5
assert b.reporte_edad().startswith("ED:2,")  # 45 h + 10 h = 2 días y pico
os.remove(ARCH)

# el cuerpo: ofrendas por comando y la súplica cuando tiene hambre
from oracool import Oracool
o = Oracool()
o.animo.archivo = ARCH
o.animo.tierra, o.animo.chispa = 10.0, 50.0
o.comando("CARA:reposo")
vistos = set()
for _ in range(40):
    o._t_turno = time.ticks_add(time.ticks_ms(), -6000)  # adelantar turnos
    o.paso()
    vistos.add(o._desfile[0])
print("con hambre desfila:", sorted(vistos))
assert "pide" in vistos and vistos <= {"ojos", "ojo", "gota", "luna", "dormido", "pide"}
o.comando("OFRENDA:barro")
assert o._efimero and o._efimero[0] == "barro"
for _ in range(10):
    o.paso()
o.animo.tierra = o.animo.chispa = 0.0
o.paso()
print("piedra:", o.animo.reporte(), "desfile:", o._desfile[:1])
try:
    os.remove(ARCH)
except OSError:
    pass
print("todo bien")
