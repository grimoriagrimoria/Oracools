# El ánima del Oracool: lo que necesita, cómo se siente y lo que recuerda.
#
# Dos necesidades que se gastan con el tiempo:
#   TIERRA  lo telúrico: el toque, el abrazo, las ofrendas de barro, agua y luna
#   CHISPA  lo sintético: las palabras, los dibujos, las ofrendas de chispa y código
# El juego es mantenerlas en equilibrio. Si las dos se apagan, el Oracool se petrifica.
import json
import time

ARCHIVO = "animo.json"

GASTO_TIERRA = 3.0   # puntos por hora
GASTO_CHISPA = 4.0   # a la máquina le da hambre más rápido
MAX_AUSENCIA = 30 * 86400  # no cobrar más de 30 días de soledad

# ofrenda -> (tierra, chispa)
OFRENDAS = {
    "barro": (25, 0),
    "agua": (15, 0),
    "luna": (10, 5),
    "chispa": (0, 25),
    "codigo": (0, 15),
    "eco": (5, 10),
    # las que llegan solas por cómo lo tratas
    "toque": (6, 0),
    "abrazo": (18, 2),
    "palabras": (0, 6),
    "dibujo": (0, 8),
}

# ánimos: código de una letra para el protocolo, nombre para las personas
RADIANTE, SERENO, TERROSO, CHISPEANTE, HAMBRIENTO, PETRIFICADO = "RSTCHP"
NOMBRES = {
    RADIANTE: "radiante", SERENO: "sereno", TERROSO: "terroso",
    CHISPEANTE: "chispeante", HAMBRIENTO: "hambriento", PETRIFICADO: "petrificado",
}


def _acotar(v):
    return 0.0 if v < 0 else 100.0 if v > 100 else v


class Animo:
    def __init__(self, archivo=ARCHIVO):
        self.archivo = archivo
        self.tierra = 60.0
        self.chispa = 60.0
        self.edad = 0          # segundos vividos (encendido + ausencias conocidas)
        self.ofrendas = 0
        self.guardado_en = None  # hora real (epoch) del último guardado, si la conocemos
        self.reloj = None        # diferencia entre la hora real y time.time()
        self._ultimo = time.ticks_ms()
        self._t_guardado = time.ticks_ms()
        self._sucio = False
        self._ausencia_cobrada = False
        self.cargar()

    # --- memoria -------------------------------------------------------
    def cargar(self):
        try:
            with open(self.archivo) as f:
                d = json.load(f)
            self.tierra = float(d.get("tierra", 60))
            self.chispa = float(d.get("chispa", 60))
            self.edad = int(d.get("edad", 0))
            self.ofrendas = int(d.get("ofrendas", 0))
            self.guardado_en = d.get("guardado_en")
        except (OSError, ValueError):
            pass  # primera vez: nace con 60 y 60

    def guardar(self):
        # sin hora real no sabemos cuándo se guardó: mejor no cobrar ausencias que cobrarlas doble
        self.guardado_en = int(time.time() + self.reloj) if self.reloj is not None else None
        d = {"tierra": round(self.tierra, 2), "chispa": round(self.chispa, 2), "edad": self.edad,
             "ofrendas": self.ofrendas, "guardado_en": self.guardado_en}
        try:
            with open(self.archivo, "w") as f:
                json.dump(d, f)
            self._sucio = False
            self._t_guardado = time.ticks_ms()
        except OSError:
            pass

    # --- el tiempo -----------------------------------------------------
    def pasar(self, segundos):
        """Envejece y gasta las necesidades por `segundos` de tiempo."""
        if segundos <= 0:
            return
        h = segundos / 3600
        self.tierra = _acotar(self.tierra - GASTO_TIERRA * h)
        self.chispa = _acotar(self.chispa - GASTO_CHISPA * h)
        self.edad += int(segundos)
        self._sucio = True

    def latir(self):
        """Llamar seguido: cobra el tiempo transcurrido y guarda de vez en cuando."""
        ahora = time.ticks_ms()
        dt = time.ticks_diff(ahora, self._ultimo)
        if dt >= 1000:
            self._ultimo = ahora
            self.pasar(dt / 1000)
        if self._sucio and time.ticks_diff(ahora, self._t_guardado) > 300_000:
            self.guardar()

    def poner_hora(self, epoch):
        """La app dice qué hora es. La primera vez, cobramos el tiempo que estuvo apagado."""
        self.reloj = epoch - time.time()
        if not self._ausencia_cobrada and self.guardado_en:
            encendido_desde = epoch - time.ticks_ms() // 1000
            ausencia = encendido_desde - self.guardado_en
            if 0 < ausencia:
                self.pasar(min(ausencia, MAX_AUSENCIA))
        self._ausencia_cobrada = True
        self.guardar()

    # --- cuidados ------------------------------------------------------
    def ofrendar(self, nombre):
        if nombre not in OFRENDAS:
            return False
        t, c = OFRENDAS[nombre]
        self.tierra = _acotar(self.tierra + t)
        self.chispa = _acotar(self.chispa + c)
        self.ofrendas += 1
        self._sucio = True
        if time.ticks_diff(time.ticks_ms(), self._t_guardado) > 30_000:
            self.guardar()
        return True

    # --- el sentir -----------------------------------------------------
    def animo(self):
        t, c = self.tierra, self.chispa
        if t < 1 and c < 1:
            return PETRIFICADO
        if min(t, c) < 20:
            return HAMBRIENTO
        if t >= 70 and c >= 70:
            return RADIANTE
        if t - c > 35:
            return TERROSO
        if c - t > 35:
            return CHISPEANTE
        return SERENO

    def reporte(self):
        """Mensaje corto (máx. 20 bytes) para la app: AN:tierra,chispa,ánimo"""
        return "AN:%d,%d,%s" % (round(self.tierra), round(self.chispa), self.animo())

    def reporte_edad(self):
        """ED:días,ofrendas"""
        return "ED:%d,%d" % (self.edad // 86400, self.ofrendas)
