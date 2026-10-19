"""Genera los íconos de la PWA a partir del ojo pixelado del Oracool (ojo.txt).

Uso:  python herramientas/iconos.py
"""
import struct
import zlib
from pathlib import Path

AQUI = Path(__file__).parent
SALIDA = AQUI.parent / "web" / "iconos"
FONDO = (0x08, 0x0a, 0x12)   # noche de Oráculos
PIXEL = (0xe3, 0xb0, 0x63)   # oro de Oráculos


def png(ancho, alto, filas):
    crudo = b"".join(b"\x00" + bytes(f) for f in filas)
    def trozo(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos))
    return (b"\x89PNG\r\n\x1a\n"
            + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
            + trozo(b"IDAT", zlib.compress(crudo, 9))
            + trozo(b"IEND", b""))


def icono(tam, margen):
    lineas = [l for l in (AQUI / "ojo.txt").read_text().splitlines() if "#" in l]
    x0 = min(l.index("#") for l in lineas)
    x1 = max(l.rindex("#") for l in lineas) + 1
    lineas = [l[x0:x1] for l in lineas]
    w, h = x1 - x0, len(lineas)
    util = tam * (1 - 2 * margen)
    paso = int(util // max(w, h))
    ox = (tam - paso * w) // 2
    oy = (tam - paso * h) // 2
    hueco = max(1, paso // 6)
    filas = []
    for y in range(tam):
        fila = bytearray()
        py, ry = divmod(y - oy, paso)
        for x in range(tam):
            px, rx = divmod(x - ox, paso)
            encendido = (0 <= py < h and 0 <= px < w and lineas[py][px] == "#"
                         and rx < paso - hueco and ry < paso - hueco)
            fila += bytes(PIXEL if encendido else FONDO)
        filas.append(fila)
    return png(tam, tam, filas)


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    for tam in (192, 512):
        (SALIDA / f"icono-{tam}.png").write_bytes(icono(tam, 0.2))
    (SALIDA / "apple-touch-icon.png").write_bytes(icono(180, 0.14))
    print("íconos listos en", SALIDA)
