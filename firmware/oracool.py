# El cuerpo del Oracool: qué muestra, cómo responde a los comandos y al toque.
#
# Comandos (texto, uno por línea):
#   HOLA              -> responde "SOY:<nombre>" y su estado
#   CARA:<glifo>      -> ojo, boca, habla, rostro, sol, tercer, dormido
#   TXT:<palabras>    -> muestra texto (si no cabe, se desplaza)
#   BRILLO:<0-255>    -> contraste de la pantalla
#   INV:<0|1>         -> invierte la pantalla
#   ESPEJO            -> manda la pantalla actual a la app
#   LIMPIA            -> pantalla en negro (modo lienzo)
# Además, si llega una pantalla completa por la característica LIENZO, la muestra.
import time
import machine
from machine import Pin
from oled42 import OLED, W, H
from glifos import GLIFOS, boca
from enlace import Enlace

_ACENTOS = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
            "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "N",
            "¿": "", "¡": ""}
_COLS, _FILAS = W // 8, H // 8  # 9 x 5 caracteres


def _sin_acentos(s):
    return "".join(_ACENTOS.get(c, c) for c in s)


def _envolver(texto):
    lineas = []
    for parrafo in _sin_acentos(texto).split("|"):
        actual = ""
        for palabra in parrafo.split():
            while len(palabra) > _COLS:
                if actual:
                    lineas.append(actual)
                    actual = ""
                lineas.append(palabra[:_COLS])
                palabra = palabra[_COLS:]
            if not actual:
                actual = palabra
            elif len(actual) + 1 + len(palabra) <= _COLS:
                actual += " " + palabra
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


class Oracool:
    def __init__(self):
        uid = machine.unique_id()
        self.nombre = "Oracool-%02X%02X" % (uid[-2], uid[-1])
        self.oled = OLED()
        self.enlace = Enlace(self.nombre, len(self.oled.buf))
        self.boton = Pin(9, Pin.IN, Pin.PULL_UP)
        self.modo = "cara"        # cara | texto | lienzo
        self.cara = "dormido"
        self.lineas = []
        self.t_texto = 0
        self.invertido = False
        self._boton_antes = 1
        self._destello = 0
        self._espejo_pendiente = False

    # --- comandos -------------------------------------------------------
    def comando(self, linea):
        clave, _, valor = linea.partition(":")
        clave = clave.strip().upper()
        if clave == "HOLA":
            self.enlace.decir("SOY:" + self.nombre)
            self.enlace.decir(self.estado())
            self._espejo_pendiente = True
        elif clave == "CARA":
            nombre = valor.strip().lower()
            if nombre in GLIFOS or nombre == "habla":
                self.modo, self.cara = "cara", nombre
                self._espejo_pendiente = True
        elif clave == "TXT":
            self.modo = "texto"
            self.lineas = _envolver(valor)
            self.t_texto = time.ticks_ms()
            self._espejo_pendiente = True
        elif clave == "BRILLO":
            self.oled.contrast(max(0, min(255, int(valor or 128))))
        elif clave == "INV":
            self.invertido = valor.strip() == "1"
            self.oled.invert(self.invertido)
        elif clave == "ESPEJO":
            self._espejo_pendiente = True
        elif clave == "LIMPIA":
            self.modo = "lienzo"
            self.oled.fill(0)
            self.oled.show()
        else:
            self.enlace.decir("?" + clave[:18])

    def estado(self):
        return "ESTADO:" + (self.cara if self.modo == "cara" else self.modo)

    # --- dibujo ---------------------------------------------------------
    def dibujar(self, t):
        fb = self.oled
        if self.modo == "lienzo":
            return False  # ya está en pantalla, no hay que redibujar
        fb.fill(0)
        if self.modo == "cara":
            if self.cara == "habla":
                boca(fb, t, hablando=True)
            else:
                GLIFOS[self.cara](fb, t)
        else:
            lineas = self.lineas
            if len(lineas) <= _FILAS:
                y0 = (H - 8 * len(lineas)) // 2
                inicio = 0
            else:
                pasos = len(lineas) - _FILAS + 1
                inicio = (time.ticks_diff(t, self.t_texto) // 1400) % (pasos + 2)
                inicio = max(0, min(inicio - 1, pasos - 1))  # pausa al inicio y al final
                y0 = 0
            for i, l in enumerate(lineas[inicio:inicio + _FILAS]):
                fb.text(l, (W - 8 * len(l)) // 2, y0 + 8 * i)
        return True

    # --- ciclo de vida --------------------------------------------------
    def _al_tocar(self):
        self.enlace.decir("TOQUE")
        if self.modo == "cara" and self.cara == "dormido":
            self.cara = "ojo"
            self.enlace.decir(self.estado())
        else:
            self._destello = time.ticks_add(time.ticks_ms(), 160)
            self.oled.invert(not self.invertido)

    def paso(self):
        e = self.enlace
        if e.cambio_conexion:
            e.cambio_conexion = False
            self.modo = "cara"
            self.cara = "ojo" if e.conectado() else "dormido"
        while e.lineas:
            try:
                self.comando(e.lineas.pop(0))
            except Exception as err:
                e.decir("ERR:" + str(err)[:16])
        if e.lienzo_listo:
            e.lienzo_listo = False
            self.modo = "lienzo"
            self.oled.buf[:] = e.lienzo
            self.oled.show()

        b = self.boton.value()
        if self._boton_antes == 1 and b == 0:
            self._al_tocar()
        self._boton_antes = b
        if self._destello and time.ticks_diff(time.ticks_ms(), self._destello) >= 0:
            self._destello = 0
            self.oled.invert(self.invertido)

        if self.dibujar(time.ticks_ms()):
            self.oled.show()
        if self._espejo_pendiente:
            self._espejo_pendiente = False
            e.espejo(self.oled.buf)

    def vivir(self):
        while True:
            self.paso()
            time.sleep_ms(40)
