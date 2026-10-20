# Enlace Bluetooth (BLE) del Oracool.
#
# Servicio "ORACOOLS" con tres características:
#   ...0002  ESCUCHA  (escritura)   comandos de texto terminados en "\n"
#   ...0003  VOZ      (notificación) eventos del Oracool: "TOQUE", "ESTADO:..."
#   ...0004  LIENZO   (escritura + notificación) pantalla cruda de 72x40,
#            en bloques: 2 bytes de posición (LE) + píxeles. La app escribe bloques de 18
#            píxeles (20 bytes); el Oracool manda bloques tan grandes como permita el MTU
#            (con el teléfono, la pantalla entera cabe en 2).
#   ...0005  ANIMA    (lectura)     "AN:tierra,chispa,ánimo" para leerlo sin suscribirse
import bluetooth
from micropython import const

_IRQ_CONECTA = const(1)
_IRQ_DESCONECTA = const(2)
_IRQ_ESCRITURA = const(3)
_IRQ_MTU = const(21)
_MTU_DESEADO = 247

_F_ESCRIBE = bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE
_F_NOTIFICA = bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY

# "ORAC" "OO" "LS" en hexadecimal
SERVICIO = bluetooth.UUID("4f524143-4f4f-4c53-8000-000000000001")
_ESCUCHA = (bluetooth.UUID("4f524143-4f4f-4c53-8000-000000000002"), _F_ESCRIBE)
_VOZ = (bluetooth.UUID("4f524143-4f4f-4c53-8000-000000000003"), _F_NOTIFICA)
_LIENZO = (bluetooth.UUID("4f524143-4f4f-4c53-8000-000000000004"), _F_ESCRIBE | _F_NOTIFICA)
_ANIMA = (bluetooth.UUID("4f524143-4f4f-4c53-8000-000000000005"), bluetooth.FLAG_READ)

BLOQUE = 18  # píxeles por bloque (20 bytes con la cabecera)


class Enlace:
    def __init__(self, nombre, tam_lienzo):
        self.nombre = nombre
        self.conexion = None
        self.lineas = []          # comandos completos esperando ser atendidos
        self.lienzo = bytearray(tam_lienzo)
        self.lienzo_listo = False
        self.cambio_conexion = False
        self._parcial = b""
        self._crudo = b""
        self.mtu = 23

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.config(gap_name=nombre)
        try:
            self._ble.config(mtu=_MTU_DESEADO)  # paquetes grandes si el otro lado puede
        except (ValueError, OSError):
            pass
        self._ble.irq(self._irq)
        ((self._h_escucha, self._h_voz, self._h_lienzo, self._h_anima),) = self._ble.gatts_register_services(
            ((SERVICIO, (_ESCUCHA, _VOZ, _LIENZO, _ANIMA)),)
        )
        # modo "append": si llegan varias escrituras seguidas no se pisan
        self._ble.gatts_set_buffer(self._h_escucha, 256, True)
        self._ble.gatts_set_buffer(self._h_lienzo, 512, True)
        self._anunciar()

    def _anunciar(self):
        n = self.nombre.encode()
        adv = bytes((2, 1, 6, len(n) + 1, 9)) + n
        resp = bytes((17, 7)) + bytes(SERVICIO)
        self._ble.gap_advertise(250_000, adv_data=adv, resp_data=resp)

    def _irq(self, evento, datos):
        if evento == _IRQ_CONECTA:
            self.conexion = datos[0]
            self.cambio_conexion = True
        elif evento == _IRQ_DESCONECTA:
            self.conexion = None
            self.cambio_conexion = True
            self.mtu = 23
            self._parcial = b""
            self._crudo = b""
            self._anunciar()
        elif evento == _IRQ_MTU:
            self.mtu = datos[1]
        elif evento == _IRQ_ESCRITURA:
            h = datos[1]
            if h == self._h_escucha:
                self._parcial += self._ble.gatts_read(h)
                while b"\n" in self._parcial:
                    linea, self._parcial = self._parcial.split(b"\n", 1)
                    self.lineas.append(linea.decode().strip())
                if len(self._parcial) > 512:
                    self._parcial = b""
            elif h == self._h_lienzo:
                self._crudo += self._ble.gatts_read(h)
                while len(self._crudo) >= 2 + BLOQUE:
                    b, self._crudo = self._crudo[:2 + BLOQUE], self._crudo[2 + BLOQUE:]
                    pos = b[0] | (b[1] << 8)
                    fin = min(pos + BLOQUE, len(self.lienzo))
                    if pos < fin:
                        self.lienzo[pos:fin] = b[2:2 + fin - pos]
                    if fin >= len(self.lienzo):
                        self.lienzo_listo = True

    def conectado(self):
        return self.conexion is not None

    def poner_anima(self, texto):
        """Deja el último reporte de ánima listo para quien lo quiera leer."""
        self._ble.gatts_write(self._h_anima, texto.encode())

    def decir(self, texto):
        """Manda un evento corto (máx. 20 bytes) a la app."""
        if self.conexion is None:
            return
        try:
            self._ble.gatts_notify(self.conexion, self._h_voz, texto.encode()[:20])
        except OSError:
            pass

    def espejo(self, buf):
        """Manda la pantalla actual a la app para que la muestre igualita."""
        if self.conexion is None:
            return
        import time
        paso = max(BLOQUE, min(len(buf), self.mtu - 5))  # 3 de ATT + 2 de posición
        for pos in range(0, len(buf), paso):
            bloque = bytes((pos & 0xFF, pos >> 8)) + buf[pos:pos + paso]
            for _ in range(3):
                try:
                    self._ble.gatts_notify(self.conexion, self._h_lienzo, bloque)
                    break
                except OSError:
                    time.sleep_ms(15)
            time.sleep_ms(4)
