"""
palomar.py · el Palomar de La Posada Real del Pinar (Pozal de Gallinas) a pluma.

Gran tambor cilíndrico de ladrillo con paños de revoco entre bandas y pilastras
de ladrillo, anillo de ventanas corrido, alero de teja muy volado (planta
octogonal, con lima al frente, como en la foto) y linterna octogonal con su
tejadillo y bola. Pinos piñoneros detrás y césped delante. Opcional: los novios
paseando (ella con velo largo, él de traje oscuro).

Perspectiva: punto de vista bajo (a ~1/4 de la altura del muro): la base se
curva hacia abajo y los anillos superiores hacia arriba. Luz desde la izquierda.
"""
import math
from pluma import Lienzo, arco_pts, rect, lerp, dist, OCRE, TERRACOTA, OLIVA
from motivos import copa, arco_3p

W, H = 700, 440
CX, R = 350.0, 212.0
Y0 = 393.0           # base del muro en el eje
HEYE = 30.0          # altura del ojo sobre la base
ALFA = 0.15          # curvatura de las elipses

H_ZOC = 8.0          # zócalo de ladrillo
BANDAS = (44.0, 88.0)
H_MURO = 130.0       # coronación del muro (bajo las ventanas)
H_VENT = 158.0       # dintel de las ventanas
H_ALERO = 172.0      # borde inferior del alero (en su radio)
R_ALERO = 1.11 * R
H_LINT = 190.0       # base de la linterna
R_LINT = 40.0
PILASTRAS = (-80.0, -31.0, 29.0, 81.0)
DELTA_P = 4.6        # semiancho angular de las pilastras (grados)


def envolvente(pts):
    """Envolvente convexa (cadena monótona)."""
    pts = sorted(set((round(x, 2), round(y, 2)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cruz(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    inf, sup = [], []
    for p in pts:
        while len(inf) >= 2 and cruz(inf[-2], inf[-1], p) <= 0:
            inf.pop()
        inf.append(p)
    for p in reversed(pts):
        while len(sup) >= 2 and cruz(sup[-2], sup[-1], p) <= 0:
            sup.pop()
        sup.append(p)
    return inf[:-1] + sup[:-1]


def P(th, h, r=R):
    """Punto del cilindro (radio r) a altura h y ángulo th (grados; 0 = de frente)."""
    t = math.radians(th)
    x = CX + r * math.sin(t)
    y = Y0 - h + (h - HEYE) * ALFA * (r / R) * (1 - math.cos(t))
    return (x, y)


def anillo(th0, th1, h, r=R, paso=3.0):
    n = max(2, int(abs(th1 - th0) / paso))
    return [P(th0 + (th1 - th0) * i / n, h, r) for i in range(n + 1)]


def octo(th, h, r):
    """Punto del alero octogonal (vértices a 0, ±45, ±90...)."""
    k = math.floor(th / 45.0)
    a0, a1 = k * 45.0, (k + 1) * 45.0
    p0, p1 = P(a0, h, r), P(a1, h, r)
    t = (th - a0) / 45.0
    # en planta los lados son rectos: interpolar en planta y proyectar
    x0, z0 = r * math.sin(math.radians(a0)), r * math.cos(math.radians(a0))
    x1, z1 = r * math.sin(math.radians(a1)), r * math.cos(math.radians(a1))
    x = x0 + (x1 - x0) * t
    z = z0 + (z1 - z0) * t
    rr = math.hypot(x, z)
    ang = math.degrees(math.atan2(x, z))
    return P(ang, h, rr)


def octo_linea(th0, th1, h, r):
    vs = [th0] + [a for a in (-90, -45, 0, 45, 90) if th0 < a < th1] + [th1]
    return [octo(a, h, r) if a not in (-90, -45, 0, 45, 90) else P(a, h, r) for a in vs]


# --------------------------------------------------------------------------
def tambor(L):
    rng = L.rng
    # siluetas laterales del tambor
    for s in (-1, 1):
        L.linea(P(90 * s, 0), P(90 * s, H_MURO + 1), peso="c")
    # base y coronación
    L.trazo(anillo(-90, 90, 0), peso="c", suave=True)
    L.trazo(anillo(-90, 90, H_ZOC), peso="d", suave=True)
    L.trazo(anillo(-90, 90, H_MURO), peso="c", suave=True)
    L.trazo(anillo(-90, 90, H_MURO - 4.5), peso="d", suave=True)
    # pilastras de ladrillo con borde dentado
    for tp in PILASTRAS:
        for s in (-1, 1):
            th = tp + s * DELTA_P
            if abs(th) >= 89.5:
                continue
            pts = []
            h = H_ZOC
            k = 0
            while h < H_MURO - 4.5:
                x, y = P(th, h)
                dx = s * (1.3 if k % 2 else 0.0)
                pts += [(x + dx, y), (x + dx, y - 4.6)]
                h += 4.6
                k += 1
            pts.append(P(th, H_MURO - 4.5))
            L.trazo(pts, peso="d", suave=False, amp=0.15, hueco=(0.3, 60))
        # hiladas de ladrillo dentro de la pilastra (sugeridas)
        with L.textura("s"):
            h = H_ZOC + 3
            k = 0
            while h < H_MURO - 7:
                if rng.random() < 0.55:
                    a = tp - DELTA_P + (1.2 if k % 2 else 0.4)
                    b = tp + DELTA_P - (0.4 if k % 2 else 1.2)
                    if abs(a) < 90 and abs(b) < 90:
                        p, q = P(a, h), P(b, h)
                        L.raya(p, q, curv=0.2)
                h += 4.6
                k += 1
    # bandas horizontales de ladrillo entre pilastras
    tramos = []
    lims = [-90.0] + [x for tp in PILASTRAS for x in (tp - DELTA_P, tp + DELTA_P)] + [90.0]
    for i in range(0, len(lims), 2):
        a, b = lims[i], lims[i + 1]
        if b - a > 2:
            tramos.append((a + 0.3, b - 0.3))
    for (a, b) in tramos:
        for hb in BANDAS:
            hb2 = hb + rng.uniform(-1.0, 1.0)
            L.trazo(anillo(a, b, hb2), peso="d", suave=True, amp=0.25)
            L.trazo(anillo(a + 0.4, b - 0.4, hb2 + 4.2), peso="s", suave=True, amp=0.25)
            with L.textura("s"):
                th = a + rng.uniform(1, 3)
                while th < b - 1:
                    p = P(th, hb2 + 0.4)
                    q = P(th, hb2 + 3.8)
                    if rng.random() < 0.6:
                        L.raya(p, (q[0] + 0.2, q[1]), curv=0)
                    th += rng.uniform(2.2, 3.4)
    # zócalo: algunas hiladas
    with L.textura("s"):
        th = -88.0
        while th < 88:
            if rng.random() < 0.45:
                a = th
                b = min(88.0, th + rng.uniform(3, 9))
                L.raya(P(a, 4.0), P(b, 4.0), curv=0.2)
            th += rng.uniform(5, 11)
    # sombra del lado derecho (rayado vertical que se aprieta hacia el borde)
    with L.textura("s", ancho=0.8):
        th = 58.0
        while th < 88.5:
            f = (th - 58.0) / 31.0
            # rayitas cortas en grupos, más largas y juntas hacia el borde
            h = H_ZOC + rng.uniform(1, 10)
            while h < H_MURO - 10:
                lg = rng.uniform(10, 26) * (0.5 + f)
                if rng.random() < 0.35 + 0.6 * f:
                    L.raya(P(th, h), P(th + rng.uniform(-0.4, 0.4), min(H_MURO - 6, h + lg)), curv=0.3)
                h += lg + rng.uniform(4, 16) * (1.2 - f)
            th += 3.6 * (1.0 - 0.7 * f) + rng.uniform(-0.4, 0.4)
    # bajante (canalón) con su embudo
    tb = -2.4
    x1 = P(tb, 0)[0]
    L.linea((x1 - 1.3, Y0 + 0.5), (x1 - 1.3, P(tb, H_ALERO - 6)[1]), peso="d")
    L.linea((x1 + 1.3, Y0 + 0.5), (x1 + 1.3, P(tb, H_ALERO - 6)[1]), peso="d")
    yt = P(tb, H_ALERO - 6)[1]
    L.linea((x1 - 1.3, yt), (x1 - 3.2, yt - 4.5), (x1 + 3.2, yt - 4.5), (x1 + 1.3, yt), peso="d")
    with L.textura("s"):
        for hh in (30.0, 70.0, 110.0):
            y = P(tb, hh)[1]
            L.raya((x1 - 3.0, y), (x1 + 3.0, y), curv=0)


def ventanas(L):
    rng = L.rng
    L.trazo(anillo(-90, 90, H_MURO + 1.6), peso="s", suave=True)
    L.trazo(anillo(-90, 90, H_VENT), peso="d", suave=True)
    th = -86.0
    k = 0
    while th <= 86.5:
        a, b = P(th, H_MURO + 1.8), P(th, H_VENT - 0.6)
        L.linea(a, b, peso="d" if k % 3 else "s", pasado=(-0.4, 0.4))
        if abs(th) < 60 and rng.random() < 0.55:
            L.linea((a[0] + 1.6, a[1] - 0.6), (b[0] + 1.6, b[1] + 0.4), peso="s", pasado=(-0.4, 0.3))
        th += 7.2 + rng.uniform(-0.3, 0.3)
        k += 1
    # sombra del alero sobre la parte alta de las ventanas + reflejos
    with L.textura("s"):
        th = -88.0
        while th < 88.0:
            top = P(th, H_VENT - 1.0)
            fr = 0.45 + 0.4 * max(0.0, th / 90.0) + rng.uniform(-0.08, 0.08)
            bot = P(th + 1.2, H_VENT - 1.0 - (H_VENT - H_MURO) * fr)
            L.raya(top, bot, curv=0.2)
            th += 1.55 * max(0.45, math.cos(math.radians(th))) + rng.uniform(-0.1, 0.1)


def alero(L):
    rng = L.rng
    # aristas del alero octogonal (borde inferior y superior del canecillo/frontal)
    ab = octo_linea(-90, 90, H_ALERO, R_ALERO)
    L.linea(*ab, peso="c")
    at = octo_linea(-90, 90, H_ALERO + 5.0, R_ALERO + 1.0)
    L.linea(*at, peso="d")
    for s in (-1, 1):
        L.linea(P(90 * s, H_ALERO, R_ALERO), P(90 * s, H_ALERO + 5.0, R_ALERO + 1.0), peso="d")
    # sofito: canes radiales en sombra
    with L.textura("s"):
        th = -88.0
        while th < 88.0:
            a = P(th, H_VENT + 0.5)
            b = octo(th, H_ALERO - 0.6, R_ALERO - 1.0)
            L.raya(a, b, curv=0.1)
            th += 3.6 * max(0.5, math.cos(math.radians(th)))
    sof = anillo(-90, 90, H_VENT + 0.6) + list(reversed(octo_linea(-90, 90, H_ALERO - 0.4, R_ALERO - 0.6)))
    L.rayado(sof, ang=118, sep=2.05, margen=(0.2, 0.6), ang_var=3)
    # tejado: borde de tejas festoneado + canales de teja + limas
    pts = []
    th = -89.5
    while th < 89.5:
        p0 = octo(th, H_ALERO + 5.4, R_ALERO + 1.0)
        th2 = th + 2.6 * max(0.35, math.cos(math.radians(th)))
        p1 = octo(min(th2, 89.5), H_ALERO + 5.4, R_ALERO + 1.0)
        m = lerp(p0, p1, 0.5)
        pts += [p0, (m[0], m[1] - 2.0)]
        th = th2
    pts.append(octo(89.5, H_ALERO + 5.4, R_ALERO + 1.0))
    L.trazo(pts, peso="s", suave=True, amp=0.12, tramo=3.0, giro=200.0)
    # faldón: canales de teja que suben hacia la linterna
    with L.textura("s"):
        th = -88.0
        while th < 88.0:
            p0 = octo(th, H_ALERO + 6.5, R_ALERO)
            p1 = octo(th, H_LINT - 2.0, R_LINT + 6.0)
            f = rng.uniform(0.18, 0.42)
            if rng.random() < 0.7:
                L.raya(p0, lerp(p0, p1, f), curv=0.3)
            th += 4.2 * max(0.4, math.cos(math.radians(th))) + rng.uniform(-0.2, 0.2)
    # limas (vértices del octógono) y contorno del faldón
    for a in (-90, -45, 0, 45, 90):
        p0 = P(a, H_ALERO + 5.0, R_ALERO + 1.0)
        p1 = P(a, H_LINT, R_LINT)
        L.linea(p0, p1, peso="d" if abs(a) < 90 else "c")
    # base de la linterna (encuentro con el faldón)
    L.linea(*[P(a, H_LINT, R_LINT) for a in (-90, -45, 0, 45, 90)], peso="d")


def linterna(L):
    rng = L.rng
    h0, h1 = H_LINT, H_LINT + 15.0
    he = h1 + 2.0
    rle = R_LINT * 1.34
    # montantes en los vértices y marco de ventanas
    for a in (-90, -45, 0, 45, 90):
        L.linea(P(a, h0, R_LINT), P(a, h1, R_LINT), peso="d" if abs(a) < 90 else "c")
    L.linea(*[P(a, h0 + 1.8, R_LINT) for a in (-90, -45, 0, 45, 90)], peso="s")
    L.linea(*[P(a, h1, R_LINT) for a in (-90, -45, 0, 45, 90)], peso="d")
    # parteluces en cada cara
    for a0 in (-90, -45, 0, 45):
        for t in (0.5,):
            am = a0 + 45 * t
            L.linea(octo(am, h0 + 2, R_LINT), octo(am, h1 - 0.5, R_LINT), peso="s")
    L.rayado([P(-90, h1, R_LINT), P(-45, h1, R_LINT), P(0, h1, R_LINT), P(45, h1, R_LINT), P(90, h1, R_LINT),
              P(90, h1 - 7, R_LINT), P(45, h1 - 6, R_LINT), P(0, h1 - 5, R_LINT), P(-45, h1 - 6, R_LINT),
              P(-90, h1 - 7, R_LINT)], ang=60, sep=1.6, margen=(0.2, 0.6))
    # alero de la linterna
    L.linea(*[P(a, he, rle) for a in (-90, -45, 0, 45, 90)], peso="c")
    L.linea(*[P(a, he + 3.5, rle + 0.6) for a in (-90, -45, 0, 45, 90)], peso="d")
    for s in (-1, 1):
        L.linea(P(90 * s, he, rle), P(90 * s, he + 3.5, rle + 0.6), peso="d")
    L.rayado([P(a, h1 + 0.4, R_LINT) for a in (-90, -45, 0, 45, 90)] +
             [P(a, he - 0.3, rle - 1) for a in (90, 45, 0, -45, -90)], ang=118, sep=1.5, margen=(0.1, 0.4))
    # tejadillo y bola
    apex = P(0, he + 16.0, 0.01)
    for a in (-90, -45, 0, 45, 90):
        L.linea(P(a, he + 3.5, rle + 0.6), apex, peso="d" if abs(a) < 90 else "c", pasado=(-0.4, 0.4))
    pts = []
    for a0 in (-90, -45, 0, 45):
        th = a0
        while th < a0 + 45:
            p0 = octo(th, he + 3.9, rle + 0.6)
            th2 = min(a0 + 45, th + 6.0 * max(0.4, math.cos(math.radians(th))))
            p1 = octo(th2, he + 3.9, rle + 0.6)
            m = lerp(p0, p1, 0.5)
            pts += arco_3p(p0, (m[0], m[1] - 1.5), p1, n=3)[:-1]
            th = th2
    pts.append(P(90, he + 3.9, rle + 0.6))
    L.trazo(pts, peso="s", suave=False, amp=0.1, tramo=8.0)
    L.linea((apex[0], apex[1]), (apex[0] + 0.2, apex[1] - 5.5), peso="d")
    L.circulo(apex[0] + 0.2, apex[1] - 8.0, 2.4, peso="d")
    L.punto(apex[0] + 0.3, apex[1] - 11.4, 0.8, peso="s")


# --------------------------------------------------------------------------
def copa_pino(L, cx, cy, w, h, fase=0.0):
    """Copa en parasol de pino piñonero: masas anchas y planas de festón menudo,
    las de delante más bajas; sombra a rayitas bajo cada masa."""
    rng = L.rng
    masas = []
    k = 5
    for i in range(k):
        t = (i + 0.5) / k * 2 - 1           # -1..1
        mx = cx + t * w * 0.36 + rng.uniform(-4, 4)
        dome = 1 - t * t
        my = cy + h * 0.18 - dome * h * 0.32 + rng.uniform(-3, 3)
        rx = w * rng.uniform(0.17, 0.22) * (1.1 if abs(t) < 0.5 else 0.95)
        ry = rx * rng.uniform(0.36, 0.44)
        masas.append((my, mx, rx, ry, abs(t)))
    # dos masas traseras más altas (la bóveda del parasol)
    for t in (-0.25, 0.3):
        mx = cx + t * w * 0.5
        masas.append((cy - h * 0.2 + rng.uniform(-3, 3), mx, w * 0.24, w * 0.24 * 0.38, 0.0))
    # orden: de delante (más bajas) a detrás
    masas.sort(key=lambda m: -m[0])
    polys = []
    for (my, mx, rx, ry, _t) in masas:
        with L.detras_de(*polys):
            poly = copa(L, mx, my, rx, ry, n=max(10, int(rx / 2.1)), peso="d", abultado=0.3,
                        irregular=0.07, aplastar_base=0.5, abierto=1)
            L.rayado(poly, ang=64, sep=2.1, margen=(0.4, 1.4),
                     largo=lambda fx, fy: max(0.0, (fy - 0.4) * 2.2), ancla="b")
        polys.append(poly)
    return polys


def pino(L, base, horca, copa_c, copa_w, copa_h, grosor=9.0):
    """Pino piñonero: tronco alto algo curvo que se abre en brazos bajo el parasol."""
    rng = L.rng
    polys = copa_pino(L, copa_c[0], copa_c[1], copa_w, copa_h)
    xb, yb = base
    tx, ty = horca
    g0, g1 = grosor / 2, grosor * 0.36
    with L.detras_de(*polys):
        mid = ((xb + tx) / 2 + (tx - xb) * 0.25 + 3.0, (yb + ty) / 2)
        L.curva([(xb - g0, yb), (mid[0] - (g0 + g1) / 2, mid[1]), (tx - g1, ty)], peso="d")
        L.curva([(xb + g0, yb), (mid[0] + (g0 + g1) / 2, mid[1]), (tx + g1, ty)], peso="d")
        # brazos
        cx, cy = copa_c
        for dx, k in ((-copa_w * 0.3, 0.9), (-copa_w * 0.05, 1.0), (copa_w * 0.26, 0.85)):
            ex, ey = tx + dx, cy + copa_h * 0.12
            mx, my = tx + dx * 0.35, ty + (ey - ty) * 0.55
            L.curva([(tx - g1 * 0.6, ty + 1), (mx - 1.6, my), (ex - 1.0, ey)], peso="d")
            L.curva([(tx + g1 * 0.6, ty + 1), (mx + 1.6, my + 0.5), (ex + 1.0, ey + 0.6)], peso="s")
        # corteza: rayitas en el lado de sombra (derecha)
        with L.textura("s"):
            n = int(abs(yb - ty) / 9)
            for i in range(n):
                f = (i + 0.5) / n
                y = yb + (ty - yb) * f
                xm = xb + (tx - xb) * f + (tx - xb) * 0.25 * math.sin(math.pi * f) * 0 + 3.0 * math.sin(math.pi * f)
                gw = g0 + (g1 - g0) * f
                L.raya((xm + gw * 0.15, y + rng.uniform(-1, 1)), (xm + gw * 0.9, y - 1.2), curv=0.3)
    return polys


def arbustos(L, x0, x1, ybase, alto, n=3):
    rng = L.rng
    polys = []
    x = x0
    for i in range(n):
        w = (x1 - x0) / n * rng.uniform(0.75, 1.1)
        with L.detras_de(*polys):
            poly = copa(L, x + w / 2, ybase - alto * 0.45, w * 0.55, alto * 0.55, n=9, peso="d",
                        abultado=0.38, aplastar_base=0.7)
            L.rayado(poly, ang=60, sep=2.2, margen=(0.5, 1.4),
                     largo=lambda fx, fy: max(0.0, (fy - 0.4) * 1.8), ancla="b")
        polys.append(poly)
        x += w * 0.8
    return polys


def novios(L, x, y, s=1.0):
    """Los novios paseando hacia la izquierda: ella de blanco con velo largo, él de traje oscuro."""
    rng = L.rng

    def T(pts, dx=0.0, dy=0.0):
        return [(x + (px + dx) * s, y + (py + dy) * s) for px, py in pts]
    # ---------------- novia (delante)
    cab_b = (x + 0.0 * s, y - 66.0 * s)
    corpino = T([(-1.2, -60.5), (-3.4, -54.0), (-2.4, -47.0)])
    espalda = T([(1.8, -61.2), (3.1, -54.0), (2.1, -47.0)])
    falda = T([(-2.4, -47.2), (-6.6, -36), (-12.6, -19), (-17.6, -4.5), (-19.6, -0.4), (-8.0, 1.8),
               (4.0, 2.0), (13.0, 1.2), (21.0, -0.4), (16.4, -5.0), (11.4, -19), (6.0, -35), (2.1, -47.2)])
    silueta_b = T([(-3.0, -70.5), (5.5, -70.5), (5.0, -60), (3.4, -54), (2.4, -47.2), (6.0, -35), (11.4, -19),
                   (16.4, -5.0), (21.0, -0.4), (13.0, 1.2), (4.0, 2.0), (-8.0, 1.8), (-19.6, -0.4),
                   (-17.6, -4.5), (-12.6, -19), (-6.6, -36), (-2.6, -46), (-9.5, -46), (-9.5, -41.5),
                   (-3.6, -40), (-3.4, -54), (-4.0, -61), (-3.8, -66)])
    velo = T([(2.6, -69.6), (5.6, -62), (8.8, -50), (12.4, -36), (17.0, -22), (23.0, -10.5), (32.0, -3.2),
              (50.0, -0.2), (72.0, 1.6), (92.0, 2.4), (98.0, 1.5)])
    velo2 = T([(97.0, 3.1), (76.0, 3.9), (52.0, 3.7), (34.0, 2.9), (22.0, 1.8)])
    poly_velo = velo + velo2
    # ---------------- novio (detrás, a la derecha)
    gx, gy = 12.5, -1.6
    cab_n = (x + gx * s, y + (gy - 72.0) * s)
    chaqueta = T([(-5.6, -64.0), (-6.1, -55), (-5.3, -46), (-5.0, -37.8), (5.4, -38.4), (5.9, -46),
                  (6.3, -55), (5.4, -64.6), (0.0, -66.2)], gx, gy)
    pierna_d = T([(-4.6, -38), (-8.2, -20), (-11.4, -2.0), (-7.0, -2.0), (-4.6, -20), (-0.4, -38)], gx, gy)
    pierna_t = T([(0.8, -38), (3.0, -20), (6.0, -2.6), (10.4, -3.0), (7.6, -20), (4.8, -38)], gx, gy)
    camisa = T([(-1.9, -65.0), (0.2, -58.5), (2.0, -65.2)], gx, gy)
    silueta_n = (T([(-4.0, -77), (4.2, -77), (4.4, -68)], gx, gy) + chaqueta[-2:-1] + chaqueta[:4] +
                 T([(-11.6, -2), (-13.2, -0.4), (11.8, -2.6), (6.3, -55)], gx, gy))
    oclusores = [silueta_b, poly_velo, silueta_n, chaqueta, pierna_d, pierna_t]
    # novia: cabeza, moño, corpiño, falda, brazo y ramo
    L.circulo(cab_b[0], cab_b[1], 3.2 * s, ry=4.0 * s, peso="d", solape=18)
    L.circulo(cab_b[0] + 3.2 * s, cab_b[1] - 1.4 * s, 1.8 * s, peso="s", solape=10)
    L.trazo(corpino, peso="d", suave=True, pasado=(-0.2, 0.3))
    L.trazo(espalda, peso="d", suave=True, pasado=(-0.2, 0.3))
    L.trazo(falda, peso="d", suave=False, pasado=(-0.3, 0.4))
    L.curva(T([(-0.6, -59.8), (-2.8, -52.5), (-6.4, -46.6)]), peso="s")
    ramo = (x - 7.8 * s, y - 45.0 * s)
    L.circulo(ramo[0], ramo[1], 2.5 * s, peso="d", solape=30)
    L.punto(ramo[0] - 0.8 * s, ramo[1] - 0.4 * s, 0.7, peso="s")
    with L.textura("s"):
        L.raya((ramo[0] - 0.5, ramo[1] + 2.4), (ramo[0] - 1.2, ramo[1] + 6.6), curv=0.1)
        L.raya((ramo[0] + 0.6, ramo[1] + 2.4), (ramo[0] + 0.6, ramo[1] + 6.8), curv=0.1)
        # pliegues de la falda
        L.raya(T([(-1.2, -44)])[0], T([(-9.0, -6)])[0], curv=0.6)
        L.raya(T([(1.0, -42)])[0], T([(2.0, -4)])[0], curv=0.5)
        L.raya(T([(2.4, -38)])[0], T([(11.5, -5)])[0], curv=0.6)
    with L.detras_de(silueta_b):
        L.trazo(velo, peso="s", suave=True, pasado=(0, 0.3), ancho=1.2)
        L.trazo(velo2, peso="s", suave=True, pasado=(0, 0.3))
    # novio
    with L.detras_de(silueta_b, poly_velo):
        L.circulo(cab_n[0], cab_n[1], 3.4 * s, ry=4.2 * s, peso="d", solape=15)
        pelo = [(cab_n[0] - 3.4 * s, cab_n[1] - 0.4 * s), (cab_n[0] - 2.4 * s, cab_n[1] - 3.9 * s),
                (cab_n[0] + 1.6 * s, cab_n[1] - 4.4 * s), (cab_n[0] + 3.6 * s, cab_n[1] - 1.4 * s),
                (cab_n[0] + 3.3 * s, cab_n[1] + 1.8 * s), (cab_n[0] + 1.0 * s, cab_n[1] - 1.0 * s)]
        L.rayado(pelo, ang=35, sep=0.9, margen=(0.0, 0.2), minimo=0.5)
        L.trazo(chaqueta, peso="d", suave=False, cerrado=True, pasado=(-0.3, 0.4))
        L.trazo(pierna_d, peso="d", suave=False, pasado=(-0.3, 0.4))
        L.trazo(pierna_t, peso="d", suave=False, pasado=(-0.3, 0.4))
        with L.detras_de(camisa + [camisa[0]]):
            L.rayado(chaqueta, ang=76, sep=1.05, margen=(0.1, 0.3), ang_var=2)
        L.rayado(pierna_d, ang=82, sep=1.1, margen=(0.1, 0.3))
        L.rayado(pierna_t, ang=82, sep=1.1, margen=(0.1, 0.3))
        L.trazo(camisa, peso="s", suave=False)
        L.linea(*T([(-13.0, -0.6), (-7.0, -0.9)], gx, gy), peso="c")
        L.linea(*T([(5.6, -2.4), (11.6, -3.2)], gx, gy), peso="c")
        L.curva(T([(-5.0, -62.5), (-7.6, -53), (-10.4, -46.5)], gx, gy), peso="d")
    return oclusores


def cesped(L, x0, x1, y0, y1, n=40):
    """Césped: unas pasadas horizontales y matas de hierba, más densas al fondo."""
    rng = L.rng
    with L.textura("s"):
        for y, a, b in ((411.0, 40, 250), (418.0, 380, 640), (426.0, 110, 330), (431.0, 470, 600)):
            x = a
            while x < b:
                lg = rng.uniform(18, 50)
                if rng.random() < 0.75:
                    L.raya((x, y + rng.uniform(-1, 1)), (min(b, x + lg), y + rng.uniform(-1, 1)), curv=0.5)
                x += lg + rng.uniform(6, 20)
        for _ in range(n):
            x = rng.uniform(x0, x1)
            t = rng.random() ** 2.2
            y = y0 + (y1 - y0) * t
            for k in range(rng.randint(2, 4)):
                bx = x + k * 1.6
                L.raya((bx, y), (bx + rng.uniform(-1.8, 1.8), y - rng.uniform(2.5, 4.8)), curv=0.4)


def paloma(L, x, y, e=1.0, ala=1.0):
    """Paloma en vuelo, a dos alas (un trazo)."""
    L.curva([(x - 7 * e, y - 1.5 * e * ala), (x - 3.5 * e, y - 3.6 * e * ala), (x - 0.4 * e, y + 0.4 * e),
             (x + 3.2 * e, y - 3.2 * e * ala), (x + 7.4 * e, y - 1.0 * e * ala)], peso="d", pasado=(0, 0.3))


def dibujar(semilla=2017, con_novios=True):
    L = Lienzo(W, H, semilla=semilla)
    rng = L.rng
    figuras = []
    if con_novios:
        figuras = novios(L, 292.0, 414.0)
    # arbustos al pie del muro (delante del tambor)
    with L.detras_de(*figuras):
        arb_i = arbustos(L, 132.0, 205.0, 395.0, 22.0, n=3)
        arb_d = arbustos(L, 505.0, 572.0, 393.0, 20.0, n=2)
    delante = figuras + arb_i + arb_d
    # edificio
    with L.detras_de(*delante):
        tambor(L)
        ventanas(L)
        alero(L)
        linterna(L)
    # silueta del edificio (para que los pinos queden detrás)
    rle = R_LINT * 1.34
    der = [P(90, -2), P(90, H_ALERO - 2, R), P(90, H_ALERO, R_ALERO), P(90, H_ALERO + 6.5, R_ALERO + 1.5),
           P(90, H_LINT, R_LINT + 1), P(90, H_LINT + 17, rle + 1), P(90, H_LINT + 21.5, rle + 1.5)]
    sil = (anillo(-90, 90, -2) + der +
           [P(0, H_LINT + 36, 0.01), P(0, H_LINT + 50, 0.01)] +
           [(2 * CX - px, py) for (px, py) in reversed(der)])
    with L.detras_de(sil, *delante):
        copa_d = pino(L, (622.0, 398.0), (606.0, 150.0), (612.0, 98.0), 190.0, 92.0, grosor=10.0)
        copa_i = pino(L, (70.0, 396.0), (80.0, 186.0), (74.0, 148.0), 150.0, 70.0, grosor=8.0)
        # línea del césped detrás del edificio y suelo
        L.trazo([(6.0, 397.0), (60.0, 396.0), (140.0, 394.5)], peso="d", suave=True)
        L.trazo([(560.0, 393.5), (640.0, 395.5), (694.0, 396.5)], peso="d", suave=True)
    with L.detras_de(*figuras):
        cesped(L, 20.0, 680.0, 399.0, 432.0, n=46)
        L.trazo([(150.0, 404.0), (300.0, 407.0), (420.0, 406.0), (560.0, 402.0)], peso="s", suave=True,
                hueco=(1.0, 50))
    paloma(L, 238.0, 112.0, 1.0)
    paloma(L, 262.0, 98.0, 0.8, ala=1.2)
    paloma(L, 452.0, 128.0, 0.7, ala=0.8)
    # aguadas
    tam = anillo(-90, 90, 0) + list(reversed(anillo(-90, 90, H_MURO)))
    L.aguada(tam, OCRE, op=0.22, dx=3.0, dy=2.0, amp=2.0)
    for tp in PILASTRAS:
        a, b = max(-89.5, tp - DELTA_P), min(89.5, tp + DELTA_P)
        L.aguada([P(a, H_ZOC), P(b, H_ZOC), P(b, H_MURO - 4), P(a, H_MURO - 4)], TERRACOTA, op=0.13,
                 dx=2.5, dy=2.0, amp=1.4, paso=9)
    techo = (octo_linea(-90, 90, H_ALERO + 5, R_ALERO + 1) +
             list(reversed([P(a, H_LINT, R_LINT) for a in (-90, -45, 0, 45, 90)])))
    L.aguada(techo, TERRACOTA, op=0.34, dx=3.0, dy=2.0, amp=1.4, paso=10)
    rle = R_LINT * 1.34
    L.aguada([P(a, H_LINT + 20.5, rle) for a in (-90, -45, 0, 45, 90)] + [P(0, H_LINT + 33, 0.01)],
             TERRACOTA, op=0.34, dx=2.4, dy=1.6, amp=0.8, paso=8)
    cesped_poly = [(14, 399), (120, 396), (350, 398), (585, 395), (690, 399), (676, 414), (560, 426),
                   (420, 432), (250, 431), (110, 424), (24, 413)]
    L.aguada(cesped_poly, OLIVA, op=0.16, dx=0, dy=1.5, amp=3.0, paso=18)
    for grupo in (copa_d, copa_i):
        env = envolvente([p for poly in grupo for p in poly])
        L.aguada(env, OLIVA, op=0.24, dx=3.0, dy=2.5, amp=3.2, paso=13)
    return L


TITULO = "El Palomar de La Posada Real del Pinar: dibujo a pluma"
