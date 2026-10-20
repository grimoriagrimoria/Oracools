# El cuerpo del Oracool: qué muestra, cómo responde a los comandos, al toque y a su ánima.
#
# Comandos (texto, uno por línea):
#   HOLA              -> responde "SOY:<nombre>", su estado y su ánima
#   HORA:<epoch>      -> la hora real (la app la manda al conectarse)
#   CARA:<glifo>      -> cualquiera de glifos.GLIFOS, "habla" o "reposo" (desfile de glifos)
#   TXT:<palabras>    -> muestra texto (si no cabe, se desplaza)
#   OFRENDA:<nombre>  -> barro, agua, luna, chispa, codigo, eco (ver animo.OFRENDAS)
#   ANIMA             -> responde "AN:tierra,chispa,ánimo" y "ED:días,ofrendas"
#   BRILLO:<0-255>    -> contraste de la pantalla
#   INV:<0|1>         -> invierte la pantalla
#   ESPEJO            -> manda la pantalla actual a la app
#   VIVO:<0|1>        -> espejo en vivo: manda la pantalla cada que cambia (unas 6 veces/s)
#   LIMPIA            -> pantalla en negro (modo lienzo)
# Además, si llega una pantalla completa por la característica LIENZO, la muestra.
#
# El botón BOOT es la mano: un toque da un poquito de tierra; sostenerlo (abrazo) da más.
import os
import time
from machine import Pin
from oled42 import OLED, W, H
from glifos import GLIFOS, POR_ANIMO, boca, CX, CY
from enlace import Enlace
from animo import Animo, PETRIFICADO, HAMBRIENTO, NOMBRES
from ofrendas import ANIMACIONES, DURACION

_ACENTOS = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
            "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "N",
            "¿": "", "¡": ""}
_COLS, _FILAS = W // 8, H // 8  # 9 x 5 caracteres
_TURNO = 3500        # ms que dura cada glifo en reposo
_TURNO_LENTO = 5500  # cuando tiene hambre todo va más despacio
_ESTATICA = 200      # ms de estática entre glifo y glifo
_ABRAZO = 1500       # ms sosteniendo el botón para que cuente como abrazo
_EFIMERO = DURACION + 1000  # ms que dura la reacción a una ofrenda: su ritual y luego su nombre
_BRILLO = 207
_BRILLO_PIEDRA = 12

# para no regalar ánima por repetir mil veces lo mismo (ms entre una y otra)
_ESPERA_GRATIS = {"toque": 20_000, "palabras": 30_000, "dibujo": 30_000}


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


def _centrar(fb, texto, y):
    fb.text(texto, (W - 8 * len(texto)) // 2, y)


class Oracool:
    def __init__(self):
        self.nombre = "Oracool"
        self.oled = OLED()
        self.enlace = Enlace(self.nombre, len(self.oled.buf))
        self.animo = Animo()
        self.boton = Pin(9, Pin.IN, Pin.PULL_UP)
        self.modo = "cara"        # cara | texto | lienzo
        self.cara = "reposo"
        self._desfile = []
        self._pozo = None         # de qué ánimo salió el desfile actual
        self._t_turno = time.ticks_ms()
        self.lineas = []
        self.t_texto = 0
        self.invertido = False
        self.brillo = _BRILLO
        self._boton_antes = 1
        self._t_presion = 0
        self._destello = 0
        self._espejo_pendiente = False
        self.vivo = False
        self._t_espejo = time.ticks_ms()
        self._ultimo_espejo = bytes(len(self.oled.buf))
        self._efimero = None      # (etiqueta, hasta)
        self._ultima_gratis = {}
        self._animo_antes = self.animo.animo()
        self._t_reporte = time.ticks_ms()
        self._aplicar_brillo()

    # --- comandos -------------------------------------------------------
    def comando(self, linea):
        clave, _, valor = linea.partition(":")
        clave = clave.strip().upper()
        valor = valor.strip()
        if clave == "HOLA":
            self.enlace.decir("SOY:" + self.nombre)
            self.enlace.decir(self.estado())
            self._reportar()
            self._espejo_pendiente = True
        elif clave == "HORA":
            self.animo.poner_hora(int(valor))
            self._reportar()
        elif clave == "CARA":
            nombre = valor.lower()
            if nombre in GLIFOS or nombre in ("habla", "reposo"):
                self.modo, self.cara = "cara", nombre
                self._espejo_pendiente = True
        elif clave == "TXT":
            self.modo = "texto"
            self.lineas = _envolver(valor)
            self.t_texto = time.ticks_ms()
            self._espejo_pendiente = True
            self._gratis("palabras")
        elif clave == "OFRENDA":
            self.ofrendar(valor.lower())
        elif clave == "ANIMA":
            self._reportar()
        elif clave == "BRILLO":
            self.brillo = max(0, min(255, int(valor or 128)))
            self._aplicar_brillo()
        elif clave == "INV":
            self.invertido = valor == "1"
            self.oled.invert(self.invertido)
        elif clave == "ESPEJO":
            self._espejo_pendiente = True
        elif clave == "VIVO":
            self.vivo = valor == "1"
            self._espejo_pendiente = True
        elif clave == "LIMPIA":
            self.modo = "lienzo"
            self.oled.fill(0)
            self.oled.show()
        else:
            self.enlace.decir("?" + clave[:18])

    def estado(self):
        return "ESTADO:" + (self.cara if self.modo == "cara" else self.modo)

    # --- ánima ----------------------------------------------------------
    def ofrendar(self, nombre, efimero=True):
        if not self.animo.ofrendar(nombre):
            self.enlace.decir("?OFRENDA")
            return
        self.enlace.decir("OF:" + nombre)
        if efimero:
            self._efimero = (nombre, time.ticks_add(time.ticks_ms(), _EFIMERO))
        self._reportar()

    def _gratis(self, nombre):
        """Ánima que llega sola por cómo lo tratas, con un respiro entre una y otra."""
        ahora = time.ticks_ms()
        antes = self._ultima_gratis.get(nombre)
        if antes is None or time.ticks_diff(ahora, antes) >= _ESPERA_GRATIS[nombre]:
            self._ultima_gratis[nombre] = ahora
            self.ofrendar(nombre, efimero=nombre == "toque")

    def _reportar(self):
        self.enlace.poner_anima(self.animo.reporte())
        self.enlace.decir(self.animo.reporte())
        self.enlace.decir(self.animo.reporte_edad())
        self._t_reporte = time.ticks_ms()

    def _aplicar_brillo(self):
        piedra = self.animo.animo() == PETRIFICADO
        self.oled.contrast(_BRILLO_PIEDRA if piedra else self.brillo)

    # --- dibujo ---------------------------------------------------------
    def _glifo_en_turno(self, t):
        """Reposo: desfilan barajados los glifos que van con su ánimo."""
        animo = self.animo.animo()
        turno = _TURNO_LENTO if animo == HAMBRIENTO else _TURNO
        if animo != self._pozo:
            self._pozo, self._desfile = animo, []
        if not self._desfile or time.ticks_diff(t, self._t_turno) >= turno:
            if len(self._desfile) <= 1:
                orden = list(POR_ANIMO[animo])
                for i in range(len(orden) - 1, 0, -1):  # barajar (Fisher-Yates)
                    j = os.urandom(1)[0] % (i + 1)
                    orden[i], orden[j] = orden[j], orden[i]
                if self._desfile and len(orden) > 1 and orden[0] == self._desfile[0]:
                    orden.append(orden.pop(0))  # que no se repita al dar la vuelta
                if animo == HAMBRIENTO:
                    orden.insert(len(orden) // 2, "pide")  # a media vuelta, pide lo que le falta
                self._desfile = orden
            else:
                self._desfile.pop(0)
            self._t_turno = t
        return self._desfile[0], time.ticks_diff(t, self._t_turno)

    def _estatica(self, f):
        """Llena la pantalla de ruido que se va apagando (f: 1 -> 0)."""
        buf = self.oled.buf
        a, b = os.urandom(len(buf)), os.urandom(len(buf))
        for i in range(len(buf)):
            buf[i] = a[i] & b[i] if f > 0.5 else a[i] & b[i] & (a[i] >> 1)

    def _pide(self, fb, t):
        falta = "tierra" if self.animo.tierra < self.animo.chispa else "chispa"
        if (t // 500) % 2:
            _centrar(fb, falta + "?", 12)
        _centrar(fb, "...", 24)

    def _dibujar_ofrenda(self, fb, etiqueta, dt):
        """Primero el ritual propio de cada ofrenda (ofrendas.py), luego su nombre y las barritas."""
        if etiqueta in ANIMACIONES and dt < DURACION:
            ANIMACIONES[etiqueta](fb, dt)
            return
        fb.ellipse(CX, 8, 3, 3, 1, True)
        t, c = self.animo.tierra, self.animo.chispa
        _centrar(fb, etiqueta, 18)
        # dos barritas: tierra a la izquierda, chispa a la derecha
        fb.rect(4, 31, 30, 5, 1)
        fb.fill_rect(5, 32, int(28 * t / 100), 3, 1)
        fb.rect(38, 31, 30, 5, 1)
        fb.fill_rect(39, 32, int(28 * c / 100), 3, 1)

    def dibujar(self, t):
        fb = self.oled
        if self._efimero:
            etiqueta, hasta = self._efimero
            if time.ticks_diff(hasta, t) > 0:
                fb.fill(0)
                self._dibujar_ofrenda(fb, etiqueta, _EFIMERO - time.ticks_diff(hasta, t))
                return True
            self._efimero = None
            if self.modo == "lienzo":
                fb.buf[:] = self.enlace.lienzo
                return True
        if self.modo == "lienzo":
            return False  # ya está en pantalla, no hay que redibujar
        fb.fill(0)
        if self.modo == "cara":
            if self.cara == "habla":
                boca(fb, t, hablando=True)
            elif self.cara == "reposo":
                nombre, dt = self._glifo_en_turno(t)
                if dt < _ESTATICA and nombre != "piedra":
                    self._estatica(1 - dt / _ESTATICA)
                elif nombre == "pide":
                    self._pide(fb, t)
                else:
                    GLIFOS[nombre](fb, t)
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

    # --- la mano --------------------------------------------------------
    def _al_presionar(self):
        self._t_presion = time.ticks_ms()
        self._destello = time.ticks_add(self._t_presion, 160)
        self.oled.invert(not self.invertido)

    def _al_soltar(self):
        sostenido = time.ticks_diff(time.ticks_ms(), self._t_presion)
        if sostenido >= _ABRAZO:
            self.enlace.decir("ABRAZO")
            self.ofrendar("abrazo")
            return
        self.enlace.decir("TOQUE")
        self._gratis("toque")
        if self.modo == "cara" and self.cara == "reposo":
            self._t_turno = time.ticks_add(time.ticks_ms(), -_TURNO_LENTO)  # salta al siguiente glifo
        elif self.modo == "cara" and self.cara == "dormido":
            self.cara = "ojo"
            self.enlace.decir(self.estado())

    # --- ciclo de vida --------------------------------------------------
    def paso(self):
        e = self.enlace
        if e.cambio_conexion:
            e.cambio_conexion = False
            self.modo = "cara"
            self.cara = "ojo" if e.conectado() else "reposo"
            if not e.conectado():
                self.vivo = False
                self.animo.guardar()
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
            self._gratis("dibujo")

        b = self.boton.value()
        if self._boton_antes == 1 and b == 0:
            self._al_presionar()
        elif self._boton_antes == 0 and b == 1:
            self._al_soltar()
        self._boton_antes = b
        if self._destello and time.ticks_diff(time.ticks_ms(), self._destello) >= 0:
            self._destello = 0
            self.oled.invert(self.invertido)

        self.animo.latir()
        animo = self.animo.animo()
        if animo != self._animo_antes:
            self.enlace.decir("ANIMO:" + NOMBRES[animo][:14])
            self._animo_antes = animo
            self._aplicar_brillo()
            self._reportar()
        elif e.conectado() and time.ticks_diff(time.ticks_ms(), self._t_reporte) > 60_000:
            self._reportar()

        if self.dibujar(time.ticks_ms()):
            self.oled.show()
        ahora = time.ticks_ms()
        cada = 160 if e.mtu >= 100 else 500  # con paquetes chiquitos, menos seguido
        en_vivo = (self.vivo and time.ticks_diff(ahora, self._t_espejo) >= cada
                   and self.oled.buf != self._ultimo_espejo)
        if self._espejo_pendiente or en_vivo:
            self._espejo_pendiente = False
            self._t_espejo = ahora
            self._ultimo_espejo = bytes(self.oled.buf)
            e.espejo(self.oled.buf)

    def vivir(self):
        while True:
            self.paso()
            time.sleep_ms(40)
