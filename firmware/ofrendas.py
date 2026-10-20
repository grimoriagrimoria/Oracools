# Cada ofrenda tiene su pequeño ritual en la pantalla.
# Cada animación es una función (fb, dt) con dt en ms desde que llegó la ofrenda,
# de 0 a DURACION; después el Oracool muestra el nombre y sus dos barritas.
from array import array
from math import sin, cos, pi
from glifos import W, H, CX, CY, cuernos

DURACION = 1700


def _azar(n):
    """Número pseudoaleatorio fijo para cada n (para que la lluvia no tiemble)."""
    n = (n * 1103515245 + 12345) & 0x7FFFFFFF
    return (n >> 8) & 0xFFFF


def barro(fb, dt):
    """La silueta del Oráculo sube desde la tierra, con terrones a los lados."""
    p = min(1, dt / 1300)
    cuernos(fb, 900)
    fb.fill_rect(0, 0, W, H - int(p * H), 0)  # se revela de abajo hacia arriba
    for i in range(6):
        x = 6 + i * 12 + (_azar(i) % 5)
        y = H - 2 - int(6 * abs(sin(dt / 160 + i)))
        fb.fill_rect(x, y, 2, 2, 1)
    fb.hline(0, H - 1, W, 1)


def agua(fb, dt):
    """Lluvia que cae y charquitos que se abren en el suelo."""
    for i in range(14):
        x = (_azar(i) % W)
        y = int((dt * 0.06 + (_azar(i + 50) % 40)) % 44) - 4
        if y < 30:
            fb.vline(x, y, 3, 1)
    fb.hline(0, 35, W, 1)
    for k in range(3):
        t0 = 250 + k * 420
        if dt > t0:
            r = int((dt - t0) / 40) % 14
            cx = 14 + k * 22
            fb.ellipse(cx, 35, r + 2, max(1, r // 4), 1, False, 1 | 2)


def luna(fb, dt):
    """La luna sube en arco y van saliendo las estrellas."""
    p = min(1, dt / 1400)
    ang = pi * (1 - p * 0.5)            # de la izquierda (180°) hasta arriba (90°)
    x = int(CX + 26 * cos(ang))
    y = int(32 - 22 * sin(ang))
    fb.ellipse(x, y, 8, 8, 1, True)
    fb.ellipse(x + 4, y - 2, 7, 7, 0, True)
    for i in range(10):
        if dt > 150 + i * 130:
            sx, sy = _azar(i) % W, _azar(i + 9) % 26
            fb.pixel(sx, sy, 1)
            if (dt // 200 + i) % 4 == 0:
                fb.pixel(sx - 1, sy, 1)
                fb.pixel(sx + 1, sy, 1)
                fb.pixel(sx, sy - 1, 1)
                fb.pixel(sx, sy + 1, 1)


_RAYO = ((40, 0), (31, 12), (39, 14), (30, 26), (37, 27), (CX, CY + 6))


def chispa(fb, dt):
    """Un rayo cae al centro, destella y revienta en chispas."""
    if dt < 380:  # el rayo baja tramo por tramo
        tramos = 1 + int(dt / 380 * (len(_RAYO) - 1))
        for a, b in zip(_RAYO[:tramos], _RAYO[1:tramos + 1]):
            fb.line(a[0], a[1], b[0], b[1], 1)
            fb.line(a[0] + 1, a[1], b[0] + 1, b[1], 1)
    elif dt < 480:  # ¡flash!
        fb.fill(1)
    else:
        k = (dt - 480) / (DURACION - 480)
        for i in range(16):
            a = i * 2 * pi / 16 + (_azar(i) % 10) / 20
            r = 3 + k * (22 + _azar(i) % 10)
            x = int(CX + r * cos(a))
            y = int(CY + 6 + r * 0.7 * sin(a))
            fb.fill_rect(x, y, 2 if i % 3 else 1, 2 if i % 3 else 1, 1)
        fb.ellipse(CX, CY + 6, max(1, int(5 * (1 - k))), max(1, int(5 * (1 - k))), 1, True)


def codigo(fb, dt):
    """Lluvia de ceros y unos, como en una terminal soñando."""
    for col in range(9):
        vel = 0.03 + (_azar(col) % 30) / 1000          # píxeles por ms
        cabeza = int(dt * vel + (_azar(col + 20) % 56)) % (H + 24) - 8
        for k in range(3):                              # la cabeza y su estela
            y = cabeza - k * 8
            if -7 < y < H:
                bit = "1" if _azar(col * 7 + k + (dt // 110)) % 2 else "0"
                fb.text(bit, col * 8, y)


def eco(fb, dt):
    """Ondas de sonido que salen hacia los lados y regresan cada vez más chiquitas."""
    fb.ellipse(CX, CY, 3, 3, 1, True)
    for k in range(3):
        t0 = k * 450
        if dt < t0:
            continue
        f = ((dt - t0) % 450) / 450
        r = int(5 + f * (30 - k * 8))
        fb.ellipse(CX, CY, r, int(r * 0.8), 1, False, 1 | 8)   # a la derecha
        fb.ellipse(CX, CY, r, int(r * 0.8), 1, False, 2 | 4)   # a la izquierda


def toque(fb, dt):
    """Una huella digital que se dibuja anillo por anillo."""
    n = min(7, 1 + dt // 170)
    for i in range(n):
        rx, ry = 2 + i * 3, 3 + int(i * 3.6)
        if i % 2:
            fb.ellipse(CX, CY + 2, rx, ry, 1, False, 1 | 2 | 4)  # anillos abiertos, como huella
        else:
            fb.ellipse(CX, CY + 2, rx, ry, 1, False, 2 | 4 | 8)
    if dt > 1250:  # al final, la huella late una vez
        r = int((dt - 1250) / 18)
        fb.ellipse(CX, CY + 2, 24 + r, 18 + r, 1)


def _corazon(fb, cx, cy, s):
    fb.ellipse(cx - s, cy, s, s, 1, True)
    fb.ellipse(cx + s, cy, s, s, 1, True)
    fb.poly(0, 0, array("h", (cx - 2 * s, cy + 1, cx + 2 * s, cy + 1, cx, cy + 2 * s + 2)), 1, True)


def abrazo(fb, dt):
    """Dos brazos se cierran alrededor de un corazón que late."""
    p = min(1, dt / 800)
    abre = int(30 - 18 * p)
    fb.ellipse(CX - abre + 12, CY, 12, 16, 1, False, 2 | 4)   # brazo izquierdo
    fb.ellipse(CX + abre - 12, CY, 12, 16, 1, False, 1 | 8)   # brazo derecho
    if dt > 600:
        latido = 1 if (dt // 220) % 2 else 0
        _corazon(fb, CX, CY - 3, 4 + latido)


ANIMACIONES = {
    "barro": barro, "agua": agua, "luna": luna,
    "chispa": chispa, "codigo": codigo, "eco": eco,
    "toque": toque, "abrazo": abrazo,
}
