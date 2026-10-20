# Se corre EN la placa: cada ofrenda corre su ritual completo sin errores (y sin tocar el animo.json real).
import os
import time
from oracool import Oracool, _EFIMERO
from ofrendas import ANIMACIONES

o = Oracool()
o.animo.archivo = "prueba_ofrendas.json"
for nombre in ANIMACIONES:
    o.comando("OFRENDA:" + nombre)
    assert o._efimero and o._efimero[0] == nombre, nombre
    t0 = time.ticks_ms()
    cuadros, peor = 0, 0
    while o._efimero:
        a = time.ticks_ms()
        o.paso()
        peor = max(peor, time.ticks_diff(time.ticks_ms(), a))
        cuadros += 1
        time.sleep_ms(30)
    print("%-7s ok  %d cuadros en %d ms, el más lento %d ms" % (nombre, cuadros, time.ticks_diff(time.ticks_ms(), t0), peor))
o._al_presionar(); o._al_soltar()
assert o._efimero and o._efimero[0] == "toque", "el botón no hizo su ritual"
try:
    os.remove("prueba_ofrendas.json")
except OSError:
    pass
print("todo bien")
