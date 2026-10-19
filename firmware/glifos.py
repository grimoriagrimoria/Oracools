# Glifos del Oracool, inspirados en los relieves de los Oráculos telúrico-sintéticos.
# Cada glifo es una función (fb, t) -> None; t es el tiempo en milisegundos,
# así cada uno decide cómo respirar, parpadear o girar.
from array import array
from math import sin, cos, pi

W, H = 72, 40
CX, CY = W // 2, H // 2


def _parpadeo(t, periodo=4200, dur=180):
    """1.0 = abierto, 0.0 = cerrado. Parpadea una vez por periodo."""
    f = t % periodo
    if f < dur:
        return abs(f - dur / 2) / (dur / 2)
    return 1.0


def _pestanas(fb, cx, cy, rx, ry, n=5, largo=6):
    for i in range(n):
        a = pi * (0.25 + 0.5 * i / (n - 1))  # abanico de 45° a 135°, sólo por arriba
        x0 = cx - int(rx * cos(a))
        y0 = cy - int(ry * sin(a))
        x1 = cx - int((rx + largo) * cos(a))
        y1 = cy - int((ry + largo) * sin(a))
        fb.line(x0, y0, x1, y1, 1)


def ojo(fb, t):
    """El ojo con pestañas que vigila (oráculo de la izquierda)."""
    a = _parpadeo(t)
    cy = CY + 4
    _pestanas(fb, CX, cy, 17, 8)
    if a < 0.25:
        fb.hline(CX - 17, cy, 35, 1)
        return
    ry = max(1, int(8 * a))
    fb.ellipse(CX, cy, 17, ry, 1)
    mirada = int(5 * sin(t / 1300))
    fb.ellipse(CX + mirada, cy, 5, min(5, ry), 1, True)
    fb.ellipse(CX + mirada - 1, cy - 1, 1, 1, 0, True)  # brillo


def boca(fb, t, hablando=False):
    """Los labios que susurran."""
    abre = 0
    if hablando:
        abre = int(3 + 3 * sin(t / 90))
    y = CY - 1
    fb.ellipse(CX - 7, y, 8, 5, 1, False, 1 | 2)    # arco izquierdo del labio de arriba
    fb.ellipse(CX + 7, y, 8, 5, 1, False, 1 | 2)    # arco derecho
    fb.ellipse(CX, y, 15, 2, 1, False, 4 | 8)       # comisura superior
    fb.ellipse(CX, y + 1 + abre, 15, 8, 1, False, 4 | 8)  # labio de abajo
    if abre:
        fb.ellipse(CX, y + 2, 11, abre, 1, True, 4 | 8)


def rostro(fb, t):
    """La carita dentro del círculo (aparece en los tres oráculos)."""
    a = _parpadeo(t, 3600)
    fb.ellipse(CX, CY, 18, 18, 1)
    fb.ellipse(CX, CY, 15, 15, 1, False, 1 | 2)     # flequillo
    for dx in (-6, 0, 6):
        fb.vline(CX + dx, CY - 15, 4, 1)
    for ex in (CX - 6, CX + 6):
        if a > 0.4:
            fb.ellipse(ex, CY - 2, 2, 2, 1, True)
        else:
            fb.hline(ex - 2, CY - 2, 5, 1)
        fb.ellipse(ex + (-3 if ex < CX else 3), CY + 5, 2, 2, 1)  # chapitas
    fb.vline(CX, CY, 4, 1)                          # nariz
    fb.hline(CX - 3, CY + 9, 7, 1)                  # boca
    fb.pixel(CX - 4, CY + 8, 1)
    fb.pixel(CX + 4, CY + 8, 1)


def sol(fb, t):
    """El sol de rayos que gira lento (oráculo del centro)."""
    giro = t / 4000
    for i in range(12):
        a = giro + 2 * pi * i / 12
        r0, r1 = 12, (19 if i % 2 else 16)
        fb.line(CX + int(r0 * cos(a)), CY + int(r0 * sin(a)),
                CX + int(r1 * cos(a)), CY + int(r1 * sin(a)), 1)
    fb.ellipse(CX, CY, 9, 9, 1)
    fb.ellipse(CX - 3, CY - 2, 1, 1, 1, True)
    fb.ellipse(CX + 3, CY - 2, 1, 1, 1, True)
    fb.hline(CX - 2, CY + 4, 5, 1)


def tercer_ojo(fb, t):
    """El triángulo con ojo y rayos (la frente del oráculo del centro)."""
    a = _parpadeo(t, 5000, 260)
    base = H - 6
    tri = array("h", (CX, 8, CX + 15, base, CX - 15, base))
    fb.poly(0, 0, tri, 1)
    for i in range(7):  # rayos en abanico sobre la punta
        ang = pi * (1.1 + 0.8 * i / 6)
        fb.line(CX + int(12 * cos(ang)), 17 + int(12 * sin(ang)),
                CX + int(16 * cos(ang)), 17 + int(16 * sin(ang)), 1)
    cy = base - 9
    if a > 0.3:
        fb.ellipse(CX, cy, 6, max(1, int(3 * a)), 1)
        fb.pixel(CX, cy, 1)
    else:
        fb.hline(CX - 6, cy, 13, 1)


def dormido(fb, t):
    """Ojos cerrados y zetas: el Oracool espera que alguien lo despierte."""
    respira = int(1.5 * sin(t / 900))
    for ex in (CX - 12, CX + 12):
        fb.ellipse(ex, CY + 2 + respira, 7, 3, 1, False, 4 | 8)
    fase = (t // 700) % 4
    for i in range(min(fase, 3)):
        fb.text("z", 52 + i * 5, 14 - i * 6)


GLIFOS = {
    "ojo": ojo,
    "boca": boca,
    "rostro": rostro,
    "sol": sol,
    "tercer": tercer_ojo,
    "dormido": dormido,
}
