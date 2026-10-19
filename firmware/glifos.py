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


def cuernos(fb, t):
    """La silueta del Oráculo de dos puntas, con las puntas que se encienden."""
    for hx in (CX - 11, CX + 11):
        fb.ellipse(hx, 7, 5, 5, 1, False, 1 | 2)
    fb.vline(CX - 16, 7, H - 7, 1)
    fb.vline(CX + 16, 7, H - 7, 1)
    fb.vline(CX - 6, 7, 16, 1)
    fb.vline(CX + 6, 7, 16, 1)
    fb.ellipse(CX, 23, 6, 5, 1, False, 4 | 8)
    lado = (t // 600) % 2
    hx = CX - 11 if lado else CX + 11
    fb.ellipse(hx, 7, 5, 5, 1, True, 1 | 2)
    a = _parpadeo(t, 3000)
    for ex in (CX - 8, CX + 8):
        if a > 0.4:
            fb.ellipse(ex, 31, 2, 2, 1, True)
        else:
            fb.hline(ex - 2, 31, 5, 1)
    fb.vline(CX, 29, 5, 1)


def rombo(fb, t):
    """El rombo de la Á del logotipo, con su barra y su punto."""
    cy, r = 16, 10
    fb.poly(0, 0, array("h", (CX, cy - r, CX + r, cy, CX, cy + r, CX - r, cy)), 1)
    k = 3 + int(2.5 * sin(t / 380))
    fb.poly(0, 0, array("h", (CX, cy - k, CX + k, cy, CX, cy + k, CX - k, cy)), 1, True)
    fb.hline(CX - 12, 31, 25, 1)
    fb.ellipse(CX - 14, 31, 2, 2, 1, True)
    fb.ellipse(CX + 14, 31, 2, 2, 1, True)
    fb.ellipse(CX, 37, 2, 2, 1, True)


_PISTAS = (
    ((6, 8), (20, 8), (28, 16), (28, 31)),
    ((66, 6), (52, 6), (45, 13), (45, 33), (59, 33)),
    ((12, 34), (36, 34), (36, 22)),
    ((36, 3), (36, 13)),
)


def _sobre(pista, f):
    """Punto a la fracción f (0..1) del recorrido de una pista."""
    tramos = [(a, b, abs(b[0] - a[0]) + abs(b[1] - a[1])) for a, b in zip(pista, pista[1:])]
    d = f * sum(l for _, _, l in tramos)
    for a, b, l in tramos:
        if d <= l:
            k = d / l if l else 0
            return int(a[0] + (b[0] - a[0]) * k), int(a[1] + (b[1] - a[1]) * k)
        d -= l
    return pista[-1]


def circuito(fb, t):
    """Las pistas de circuito del logotipo, con chispas que las recorren."""
    for i, p in enumerate(_PISTAS):
        for a, b in zip(p, p[1:]):
            fb.line(a[0], a[1], b[0], b[1], 1)
        for x, y in (p[0], p[-1]):
            fb.ellipse(x, y, 2, 2, 1)
            fb.pixel(x, y, 0)
        x, y = _sobre(p, ((t / 1400) + i * 0.27) % 1)
        fb.fill_rect(x - 1, y - 1, 3, 3, 1)


def espiral(fb, t):
    """El caracol del tiempo que gira hacia adentro."""
    giro = -t / 700
    x0, y0 = CX, CY
    th = 0.0
    while th < 6 * pi:
        r = 0.95 * th
        x1 = CX + int(r * cos(th + giro))
        y1 = CY + int(0.9 * r * sin(th + giro))
        fb.line(x0, y0, x1, y1, 1)
        x0, y0 = x1, y1
        th += 0.45


_ASTROS = ((50, 6), (62, 14), (56, 30), (66, 34), (8, 6), (44, 20), (14, 34), (68, 4))


def _estrella(fb, x, y, grande):
    fb.pixel(x, y, 1)
    if grande:
        fb.hline(x - 2, y, 5, 1)
        fb.vline(x, y - 2, 5, 1)


def luna(fb, t):
    """La luna creciente con estrellas que titilan."""
    fb.ellipse(26, CY, 13, 13, 1, True)
    fb.ellipse(31, CY - 3, 12, 12, 0, True)
    for i, (x, y) in enumerate(_ASTROS):
        _estrella(fb, x, y, ((t // 350) + i * 3) % 5 == 0)


def cielo(fb, t):
    """Un cielo de estrellas con una fugaz de vez en cuando."""
    s = 7
    for i in range(22):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        x, y = s % W, (s >> 8) % H
        brilla = ((t // 280) + i * 5) % 9
        if brilla:
            _estrella(fb, x, y, brilla == 1)
    f = (t % 3200) / 1100
    if f < 1:
        x = int(70 - 60 * f)
        y = int(4 + 18 * f)
        fb.line(x, y, x + 8, y - 3, 1)


def gota(fb, t):
    """El escurrimiento del Oráculo de la derecha: una gota que cae."""
    fb.fill_rect(CX - 1, 0, 3, 16, 1)
    f = (t % 1800) / 1800
    if f < 0.55:
        r = int(1 + 3 * f / 0.55)
        fb.ellipse(CX, 16 + r, r, r + 1, 1, True)
    elif f < 0.85:
        y = int(20 + (f - 0.55) / 0.3 * 15)
        fb.ellipse(CX, y, 3, 4, 1, True)
    else:
        k = int((f - 0.85) / 0.15 * 8)
        fb.ellipse(CX, 38, 3 + k, 2, 1, False, 1 | 2)
        fb.pixel(CX - 4 - k, 33 - k // 2, 1)
        fb.pixel(CX + 4 + k, 33 - k // 2, 1)


def dos_ojos(fb, t):
    """La mirada doble del Oráculo del centro."""
    a = _parpadeo(t, 3300)
    mirada = int(4 * sin(t / 900))
    for ex in (CX - 15, CX + 15):
        if a < 0.3:
            fb.hline(ex - 10, CY, 21, 1)
            continue
        ry = max(1, int(6 * a))
        fb.ellipse(ex, CY, 10, ry, 1)
        fb.ellipse(ex + mirada, CY, 3, min(3, ry), 1, True)
        fb.pixel(ex + mirada - 1, CY - 1, 0)


def nariz(fb, t):
    """La nariz del Oráculo de la izquierda, que respira."""
    aire = int(1.5 + 1.5 * sin(t / 600))
    fb.line(CX - 4, 3, CX - 6, 24, 1)
    fb.line(CX + 4, 3, CX + 6, 24, 1)
    fb.ellipse(CX - 8, 29, 5 + aire, 5, 1, False, 2 | 4 | 8)
    fb.ellipse(CX + 8, 29, 5 + aire, 5, 1, False, 1 | 4 | 8)
    fb.ellipse(CX, 30, 4, 4, 1, False, 1 | 2)
    fb.ellipse(CX - 8, 31, 2 + aire // 2, 1, 1, True)
    fb.ellipse(CX + 8, 31, 2 + aire // 2, 1, 1, True)


def orbe(fb, t):
    """La O del logotipo: anillo partido con su punto al centro."""
    fb.ellipse(CX, CY, 15, 18, 1, True)
    fb.ellipse(CX, CY, 10, 13, 0, True)
    fb.fill_rect(CX - 2, 0, 5, 9, 0)
    fb.fill_rect(CX - 2, H - 9, 5, 9, 0)
    fb.vline(CX, 0, 6, 1)
    fb.vline(CX, H - 6, 6, 1)
    r = 3 + int(1.5 * (1 + sin(t / 300)))
    fb.ellipse(CX, CY, r, r, 1, True)


def runa(fb, t):
    """La U del logotipo: eje con círculo, cruz y punto que viaja."""
    fb.vline(CX, 2, 34, 1)
    fb.ellipse(CX, 16, 7, 7, 0, True)
    fb.ellipse(CX, 16, 7, 7, 1)
    fb.ellipse(CX, 16, 2, 2, 1, True)
    fb.hline(CX - 5, 29, 11, 1)
    fb.ellipse(CX, 2, 2, 2, 1, True)
    y = int(24 + 12 * ((t % 1500) / 1500))
    fb.fill_rect(CX - 1, y, 3, 2, 1)
    for lado in (-1, 1):  # la V que abraza a la runa
        fb.line(CX + lado * 17, 2, CX + lado * 6, 36, 1)


def onda(fb, t):
    """Ondas que nacen del centro, como piedra en el agua."""
    for k in range(4):
        r = int((t / 45 + k * 9) % 36)
        if r > 1:
            fb.ellipse(CX, CY, r, int(r * 0.75), 1)
    fb.ellipse(CX, CY, 2, 2, 1, True)


GLIFOS = {
    "ojo": ojo,
    "boca": boca,
    "rostro": rostro,
    "sol": sol,
    "tercer": tercer_ojo,
    "cuernos": cuernos,
    "rombo": rombo,
    "circuito": circuito,
    "espiral": espiral,
    "luna": luna,
    "cielo": cielo,
    "gota": gota,
    "ojos": dos_ojos,
    "nariz": nariz,
    "orbe": orbe,
    "runa": runa,
    "onda": onda,
    "dormido": dormido,
}

# los que desfilan cuando el Oracool está en reposo
REPOSO = [n for n in GLIFOS if n != "dormido"]
