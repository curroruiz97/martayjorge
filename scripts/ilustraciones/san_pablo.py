"""
san_pablo.py · fachada de la Iglesia de San Pablo (Valladolid) a pluma.

Proporciones tomadas de la referencia (acuarela y fotos): dos torres lisas de
sillería con cuerpo de campanas, piñón con cresterías y cruz, retablo central
(cuadrícula de hornacinas y escudos), rosetón dentro de un arco conopial, gran
arco conopial de la portada, portada abocinada con arquivoltas y parteluz.
Luz desde arriba a la izquierda: sombras a la derecha/abajo de los volúmenes.
"""
import math
from pluma import Lienzo, arco_pts, rect, lerp, OCRE, TERRACOTA, OLIVA
from motivos import (apuntado, apuntado_pts, conopial_pts, cresteria, pinaculo, estatua,
                     dosel, nicho, santo, escudo, roseton, copa, festones_interiores)

W, H = 520, 620
CX = 260.0
BASE = 578.0        # arranque de los muros (sobre las gradas)
ZOCALO = 566.0

TI = (82.0, 163.0)   # torre izquierda
TD = (357.0, 438.0)  # torre derecha
TOP_I, TOP_D = 160.0, 157.0
COR_C = 176.0        # cornisa del cuerpo central
APEX = (CX, 104.0)   # vértice del piñón
CONT_I = (163.0, 177.0)   # contrafuertes del retablo
CONT_D = (343.0, 357.0)


# --------------------------------------------------------------------------
def sillares(L, x0, x1, y0, y1, lado):
    """Sillería sugerida: cadenas de sillares en las esquinas, por tramos, y alguna hilada suelta."""
    rng = L.rng
    hil = 11.6
    w = x1 - x0
    ys = []
    y = y0
    while y < y1 - 4:
        ys.append(y)
        y += hil + rng.uniform(-0.7, 0.7)
    with L.textura("s"):
        for borde in ((0,) if lado < 0 else (1,)):
            k = rng.randint(0, 3)
            while k < len(ys) - 2:
                run = rng.randint(3, 6)
                largo_par = rng.uniform(0.26, 0.34) * w
                largo_imp = rng.uniform(0.14, 0.2) * w
                for j in range(run):
                    if k + j >= len(ys) - 1:
                        break
                    yy = ys[k + j]
                    lg = largo_par if (k + j) % 2 == 0 else largo_imp
                    if borde == 0:
                        a, b = x0 + 0.8, x0 + lg
                    else:
                        a, b = x1 - lg, x1 - 0.8
                    L.raya((a, yy), (b, yy + rng.uniform(-0.5, 0.5)), curv=0.25)
                    # junta vertical hasta la hilada siguiente (solo si sigue el tramo)
                    if j < run - 1 and k + j + 1 < len(ys):
                        jx = b if borde == 0 else a
                        L.raya((jx, yy + 0.4), (jx + rng.uniform(-0.4, 0.4), ys[k + j + 1] - 0.4), curv=0.1)
                # última hilada del tramo
                if k + run < len(ys):
                    yy = ys[k + run]
                    lg = largo_par if (k + run) % 2 == 0 else largo_imp
                    a, b = (x0 + 0.8, x0 + lg) if borde == 0 else (x1 - lg, x1 - 0.8)
                    L.raya((a, yy), (b, yy), curv=0.25)
                k += run + rng.randint(3, 7)
        # hiladas sueltas por el centro (pocas)
        for yy in ys:
            if rng.random() < 0.22:
                a = rng.uniform(x0 + w * 0.2, x0 + w * 0.5)
                L.raya((a, yy), (a + rng.uniform(10, 26), yy + rng.uniform(-0.5, 0.5)), curv=0.3)


def torre(L, x0, x1, ytop, lado, reloj=False):
    rng = L.rng
    xc = (x0 + x1) / 2
    L.linea((x0, BASE + 1), (x0, ytop), peso="c")
    L.linea((x1, BASE + 1), (x1, ytop), peso="c")
    # cornisa principal con su sombra
    L.linea((x0 - 4.5, ytop - 6.5), (x1 + 4.5, ytop - 6.5), peso="c")
    L.linea((x0 - 4.5, ytop - 6.5), (x0 - 3.2, ytop), (x1 + 3.2, ytop), (x1 + 4.5, ytop - 6.5), peso="d")
    L.linea((x0 + 0.5, ytop + 5), (x1 - 0.5, ytop + 5), peso="s")
    L.rayado(rect(x0 + 0.5, ytop + 0.5, x1 - 0.5, ytop + 4.8), ang=62, sep=2.2, margen=(0.2, 0.8))
    # impostas
    impostas = (272.0 + rng.uniform(-2, 2), 470.0 + rng.uniform(-2, 2))
    for yi in impostas:
        L.linea((x0 - 2, yi), (x1 + 2, yi), peso="d")
        L.linea((x0 - 1.5, yi + 4.2), (x1 + 1.5, yi + 4.2), peso="d")
        L.rayado(rect(x0 + 1, yi + 4.6, x1 - 1, yi + 8.0), ang=62, sep=2.5, prob=0.85, margen=(0.2, 1.0))
    L.linea((x0, ZOCALO), (x1, ZOCALO), peso="d")
    # sillería por tramos entre impostas
    sillares(L, x0, x1, ytop + 14, impostas[0] - 2, lado)
    sillares(L, x0, x1, impostas[0] + 16, impostas[1] - 2, lado)
    sillares(L, x0, x1, impostas[1] + 16, ZOCALO - 2, lado)
    # vanos
    ventana_arco(L, xc + rng.uniform(-2, 2), 420 + rng.uniform(-3, 3), 11, 25)
    tablero(L, xc + rng.uniform(-2, 2), 452 + rng.uniform(-2, 2), 20, 16)
    if reloj:
        cy = 206
        L.circulo(xc, cy, 12.5, peso="d")
        L.circulo(xc, cy, 10.0, peso="s")
        L.linea((xc, cy), (xc - 3.0, cy - 6.0), peso="d", pasado=(0, 0.3))
        L.linea((xc, cy), (xc + 5.0, cy + 1.5), peso="d", pasado=(0, 0.3))
        with L.textura("s"):
            for k in range(12):
                a = math.radians(k * 30)
                L.raya((xc + 7.8 * math.cos(a), cy + 7.8 * math.sin(a)),
                       (xc + 9.3 * math.cos(a), cy + 9.3 * math.sin(a)), curv=0)
    else:
        L.linea((xc - 1.7, 222), (xc - 1.7, 250), peso="d")
        L.linea((xc + 1.7, 222), (xc + 1.7, 250), peso="d")
        L.rayado(rect(xc - 1.5, 222.5, xc + 1.5, 249.5), ang=80, sep=1.2, margen=(0, 0.2))


def ventana_arco(L, x, yb, w, h):
    ys = yb - h + w / 2
    pts = [(x - w / 2, yb)] + arco_pts(x, ys, w / 2, w / 2, 180, 0, n=8) + [(x + w / 2, yb)]
    L.trazo(pts, peso="d", suave=False)
    L.linea((x - w / 2 - 2, yb + 0.5), (x + w / 2 + 2, yb + 0.5), peso="d")
    L.rayado(pts, ang=72, sep=1.8, margen=(0.3, 0.9))


def tablero(L, x, y, w, h):
    L.linea((x - w / 2, y + h / 2), (x - w / 2, y - h / 2), (x + w / 2, y - h / 2), peso="d")
    L.linea((x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2), peso="d")
    L.linea((x - w / 2 + 3, y + h / 2 - 3), (x - w / 2 + 3, y - h / 2 + 3), (x + w / 2 - 3, y - h / 2 + 3), peso="s")


def campanario(L, x0, x1, ybase, ytop, lado):
    rng = L.rng
    xc = (x0 + x1) / 2 + rng.uniform(-0.8, 0.8)
    L.linea((x0, ybase), (x0, ytop), peso="c")
    L.linea((x1, ybase), (x1, ytop), peso="c")
    L.linea((x0 + 4.5, ybase - 1), (x0 + 4.5, ytop + 4), peso="s")
    L.linea((x1 - 4.5, ybase - 1), (x1 - 4.5, ytop + 4), peso="s")
    # vano de medio punto con la campana en oscuro
    r = 13.0
    ys = ytop + 27
    sill = ybase - 6
    arco = arco_pts(xc, ys, r, r, 180, 0, n=10)
    hueco = [(xc - r, sill)] + arco + [(xc + r, sill)]
    L.trazo(hueco, peso="d", suave=False)
    L.linea((xc - r - 3, sill), (xc + r + 3, sill), peso="d")
    L.linea((xc - r - 2.5, ys), (xc - r + 0.6, ys), peso="s")
    L.linea((xc + r - 0.6, ys), (xc + r + 2.5, ys), peso="s")
    by = ys - 5
    bell = [(xc - 3.0, by + 1.5), (xc - 4.4, by + 6.5), (xc - 5.3, by + 12.5), (xc - 6.6, by + 17),
            (xc - 9.0, by + 20.0), (xc + 9.0, by + 20.0), (xc + 6.6, by + 17), (xc + 5.3, by + 12.5),
            (xc + 4.4, by + 6.5), (xc + 3.0, by + 1.5)]
    L.trazo(bell, peso="d", suave=True, pasado=(-0.2, 0.4))
    L.linea((xc - 8.5, by + 0.6), (xc + 8.5, by + 0.2), peso="d")      # yugo
    L.linea((xc, ys - r + 1), (xc, by + 0.4), peso="s")                 # colgadero
    L.rayado(bell, ang=82, sep=1.25, margen=(0.1, 0.4), ang_var=2)
    L.rayado(bell, ang=28, sep=2.6, margen=(0.3, 0.8), ang_var=3, prob=0.8)
    L.punto(xc + 0.6, by + 22.0, 1.2, peso="d")                         # badajo
    # sombra en el intradós del vano
    sombra = arco_pts(xc, ys, r, r, 180, 0, n=10) + list(reversed(arco_pts(xc + 2.0, ys + 3.0, r - 1.2, r - 3.0, 180, 0, n=10)))
    L.rayado(sombra, ang=70, sep=1.7, margen=(0.1, 0.5))
    L.rayado(rect(xc - r + 0.5, ys, xc - r + 3.5, sill - 0.5), ang=70, sep=2.2, margen=(0.1, 0.5))
    # cornisa del campanario
    L.linea((x0 - 3.5, ytop - 5), (x1 + 3.5, ytop - 5), peso="d")
    L.linea((x0 - 3.5, ytop - 5), (x0 - 2.5, ytop), (x1 + 2.5, ytop), (x1 + 3.5, ytop - 5), peso="d")
    L.rayado(rect(x0 + 0.5, ytop + 0.4, x1 - 0.5, ytop + 4), ang=62, sep=2.1, margen=(0.2, 0.6))
    # frontón y remates (pirámides con bola)
    ap = ytop - 5 - rng.uniform(15, 18)
    L.linea((x0 - 2, ytop - 5.5), (xc, ap), (x1 + 2, ytop - 5.5), peso="d")
    for x, top in ((x0 + 0.5, ytop - 23), (x1 - 0.5, ytop - 22), (xc, ap - 14)):
        top += rng.uniform(-1.5, 1.5)
        yb = ytop - 5.5 if x != xc else ap
        L.linea((x - 2.2, yb), (x - 2.2, yb - 3.2), (x + 2.2, yb - 3.2), (x + 2.2, yb), peso="s")
        L.linea((x - 1.8, yb - 3.2), (x, top + 2.4), (x + 1.8, yb - 3.2), peso="d")
        L.punto(x, top + 1.0, 1.1, peso="d")


def arqueria(L, x0, x1, y, paso=6.0, alto=3.0, peso="s"):
    """Crestería bajo cornisa: festón de arquillos en una sola línea."""
    rng = L.rng
    pts = []
    x = x0
    while x < x1 - 1:
        pts += arco_pts(x + paso / 2, y, paso / 2, alto, 180, 0, n=4)[:-1]
        x += paso * rng.uniform(0.95, 1.05)
    pts.append((x, y))
    L.trazo(pts, peso=peso, suave=False, pasado=(-0.2, 0.4), amp=0.15)


def cuerpo_central(L):
    rng = L.rng
    x0, x1 = TI[1], TD[0]
    # --- contrafuertes con retallos y pinaculillos
    for xa, xb, s in (CONT_I + (-1,), CONT_D + (1,)):
        xi = xb if s < 0 else xa
        L.linea((xi, ZOCALO), (xi, COR_C + 2), peso="d")
        for yr in (318.0, 440.0):
            L.linea((xa + 0.5, yr), (xb - 0.5, yr), peso="s")
            L.linea((xa + 1, yr - 3), (xb - 1, yr - 3), peso="s")
            pinaculo(L, (xa + xb) / 2, yr - 3, yr - 30, 5.0, peso="s", ganchos_n=1)
    # --- cornisa central, arquería y piñón
    L.linea((x0, COR_C), (x1, COR_C), peso="c")
    L.linea((x0 + 1, COR_C - 4.2), (x1 - 1, COR_C - 4.2), peso="d")
    arqueria(L, 178.0, 342.0, COR_C + 5.0)
    L.rayado(rect(177.5, COR_C + 0.5, 342.5, COR_C + 4.6), ang=62, sep=2.3, margen=(0.2, 0.8))
    izq = [(171.0, COR_C - 4.5), APEX]
    der = [APEX, (349.0, COR_C - 4.5)]
    L.linea(*izq, peso="c")
    L.linea(*der, peso="c")
    L.linea((183.0, COR_C - 6.5), (CX, APEX[1] + 10.5), (337.0, COR_C - 6.5), peso="s")
    cresteria(L, [lerp(izq[0], izq[1], t / 30) for t in range(31)], cada=8.0, alto=4.4, peso="d", lado=1,
              hasta=0.93)
    cresteria(L, [lerp(der[1], der[0], t / 30) for t in range(31)], cada=8.0, alto=4.4, peso="d", lado=-1,
              hasta=0.93)
    escudo(L, CX, 146.0, 24.0, 27.0, peso="d")
    pinaculo(L, 170.0, COR_C - 4.5, 124.0, 6.4, peso="d", ganchos_n=2)
    pinaculo(L, 350.0, COR_C - 4.5, 127.0, 6.4, peso="d", ganchos_n=2)
    # cruz de remate (un pelín inclinada)
    L.circulo(CX, APEX[1] - 3.0, 2.6, peso="d")
    L.linea((CX + 0.2, APEX[1] - 5.8), (CX + 1.0, 44.0), peso="c", pasado=(0, 1.2))
    L.linea((CX - 9.0, 61.6), (CX + 10.0, 60.8), peso="c", pasado=(0, 1.0))
    # --- retablo superior: cuadrícula de calles y cuerpos
    for xv in (218.0, 302.0):
        L.linea((xv - 1.5, COR_C + 9), (xv - 1.5, 318.0), peso="d")
        L.linea((xv + 1.5, COR_C + 9), (xv + 1.5, 318.0), peso="s")
    for yh in (224.0, 271.0, 318.0):
        L.linea((177.5, yh), (342.5, yh), peso="d")
        L.linea((178.0, yh + 3.2), (342.0, yh + 3.2), peso="s")
        if yh < 300:
            arqueria(L, 179.0, 341.0, yh + 7.0, paso=5.5, alto=2.4)
    for xv in (218.0, 302.0):
        for yh in (224.0, 271.0):
            pinaculo(L, xv, yh - 0.5, yh - 16, 3.2, peso="s", ganchos_n=0)
    # cuerpo 1: escudos grandes a los lados, tres hornacinas en el centro
    escudo(L, 197.5, 203.0, 22.0, 26.0, peso="d")
    escudo(L, 322.5, 203.0, 22.0, 26.0, peso="d")
    for x, h in ((235.0, 24.0), (252.0, 25.0), (268.0, 25.0), (285.0, 24.0)):
        santo(L, x, 217.0, h, dosel_w=12.0)
    for xp in (243.5, 260.0, 276.5):
        pinaculo(L, xp, 219.0, 186.0, 2.6, peso="s", ganchos_n=0, bola=False)
    # cuerpo 2: santos a los lados; escudo con tenantes en el centro
    santo(L, 197.5, 264.0, 26.0, dosel_w=15.0)
    santo(L, 322.5, 264.0, 26.0, dosel_w=15.0)
    escudo(L, CX, 249.0, 22.0, 26.0, peso="d", lambrequin=False)
    estatua(L, 236.0, 266.0, 27.0, gira=1.0, peso="d")
    estatua(L, 284.0, 266.0, 27.0, gira=-1.0, peso="d")
    # cuerpo 3
    santo(L, 197.5, 311.0, 25.0, dosel_w=15.0)
    santo(L, 322.5, 311.0, 25.0, dosel_w=15.0)
    santo(L, 234.0, 311.0, 22.0, dosel_w=11.0)
    santo(L, 286.0, 311.0, 22.0, dosel_w=11.0)
    # --- rosetón dentro de su conopial con cresterías
    roseton(L, CX, 357.0, 23.0)
    izq, der = conopial_pts(CX, 33.0, 402.0, 80.0, hombro=0.8, punta=0.55)
    L.trazo([(CX - 33.0, 409.0)] + izq + der[1:] + [(CX + 33.0, 409.0)], peso="d", suave=False)
    iz2, de2 = conopial_pts(CX, 28.5, 402.0, 71.0, hombro=0.8, punta=0.55, n=12)
    L.trazo(iz2 + de2[1:], peso="s", suave=False)
    cresteria(L, izq, cada=7.2, alto=3.8, lado=1, desde=0.25, hasta=0.9)
    cresteria(L, list(reversed(der)), cada=7.2, alto=3.8, lado=-1, desde=0.25, hasta=0.9)
    pinaculo(L, CX, 322.0, 302.0, 3.4, peso="d", ganchos_n=1)
    # a los lados del rosetón: santos bajo dosel y escudos
    santo(L, 199.0, 372.0, 30.0, dosel_w=16.0)
    santo(L, 321.0, 372.0, 30.0, dosel_w=16.0)
    for xp in (184.0, 214.0, 306.0, 336.0):
        pinaculo(L, xp, 376.0, 334.0, 2.8, peso="s", ganchos_n=1, bola=False)
    # --- gran arco conopial de la portada
    xa, xb = 194.0, 326.0
    izq, der = conopial_pts(CX, 66.0, 478.0, 58.0, hombro=0.92, punta=0.62, n=18)
    L.trazo(izq + der[1:], peso="c", suave=False)
    iz2, de2 = conopial_pts(CX, 58.5, 480.0, 50.0, hombro=0.92, punta=0.62, n=16)
    L.trazo(iz2 + de2[1:], peso="d", suave=False)
    cresteria(L, izq, cada=7.8, alto=4.6, peso="d", lado=1, desde=0.12, hasta=0.95)
    cresteria(L, list(reversed(der)), cada=7.8, alto=4.6, peso="d", lado=-1, desde=0.12, hasta=0.95)
    pinaculo(L, CX, 420.0, 386.0, 4.4, peso="d", ganchos_n=3)
    L.linea((xa, 478.0), (xa, ZOCALO), peso="c")
    L.linea((xb, 478.0), (xb, ZOCALO), peso="c")
    L.linea((xa + 7.5, 480.0), (xa + 7.5, ZOCALO), peso="d")
    L.linea((xb - 7.5, 480.0), (xb - 7.5, ZOCALO), peso="d")
    banda = izq + der[1:] + list(reversed(iz2 + de2[1:]))
    L.rayado(banda, ang=58, sep=2.2, margen=(0.2, 0.8), largo=lambda fx, fy: 1.0 if fx < 0.6 else 0.5)
    L.rayado(rect(xa + 0.8, 482.0, xa + 6.8, ZOCALO - 1), ang=66, sep=2.3, margen=(0.2, 0.7))
    # tímpano: Coronación de la Virgen (sugerida) sobre una repisa
    L.linea((xa + 8, 479.0), (xb - 8, 479.0), peso="d")
    estatua(L, 251.5, 476.0, 21.0, gira=0.8, peso="d", sentada=True, nimbo=True)
    estatua(L, 268.5, 476.0, 21.0, gira=-0.8, peso="d", sentada=True, nimbo=True)
    L.trazo([(255.0, 447.5), (256.0, 443.5), (258.2, 446.0), (260.0, 442.0), (261.8, 446.0),
             (264.0, 443.5), (265.0, 447.5), (255.0, 447.5)], peso="s", suave=False)
    for x, h in ((225.0, 17.0), (237.0, 19.0), (283.0, 19.0), (295.0, 17.0)):
        estatua(L, x + rng.uniform(-0.8, 0.8), 476.0, h, gira=rng.uniform(-1, 1), nimbo=True)
    for x, s in ((213.0, 1), (307.0, -1)):
        # ángeles: alas sugeridas
        L.curva([(x - 3 * s, 474), (x - 1 * s, 466), (x + 3 * s, 462), (x + 5 * s, 465)], peso="s")
        L.curva([(x - 1 * s, 474), (x + 2 * s, 468), (x + 5 * s, 468)], peso="s")
    # --- portada abocinada: arquivoltas apuntadas y puerta con parteluz
    ys = 544.0
    for (a, b) in ((216.0, 304.0), (224.0, 296.0), (232.0, 288.0)):
        apuntado(L, a, b, ys, k=0.72, peso="d", jambas=ZOCALO)
    iz, de = apuntado_pts(220.0, 300.0, ys, k=0.72, n=9)
    with L.textura("s"):
        for p in (iz + de[1:])[1:-1]:
            L.raya((p[0] - 0.8, p[1] + 0.5), (p[0] + 0.8, p[1] - 0.5), curv=0)
    iz, de = apuntado_pts(240.0, 280.0, ys, k=0.72, n=8)
    puerta = [(240.0, ZOCALO)] + iz + de[1:] + [(280.0, ZOCALO)]
    L.trazo(puerta, peso="c", suave=False)
    # parteluz con la imagen sobre peana y doselete
    estatua(L, CX, 560.0, 36.0, peso="d")
    L.linea((253.0, 560.0), (267.0, 560.0), peso="d")
    L.linea((254.5, 560.0), (254.5, ZOCALO), peso="d")
    L.linea((265.5, 560.0), (265.5, ZOCALO), peso="d")
    dosel(L, CX, 520.0, 14.0, peso="d")
    figura = [(252.0, 562.0), (252.0, 519.0), (268.0, 519.0), (268.0, 562.0), (266.5, 562.0),
              (266.5, 580.0), (253.5, 580.0), (253.5, 562.0)]
    with L.detras_de(figura):
        L.rayado(puerta, ang=84, sep=1.8, margen=(0.2, 0.8), ang_var=3)
        L.rayado(puerta, ang=18, sep=4.0, margen=(0.5, 1.5), prob=0.7, ang_var=4)
    # santos en las jambas
    for x in (208.5, 311.5):
        santo(L, x, 538.0, 25.0, dosel_w=11.0, sombra=False)
    # hornacinas junto a la portada
    santo(L, 185.5, 556.0, 30.0, dosel_w=11.0)
    santo(L, 334.5, 556.0, 30.0, dosel_w=11.0)
    santo(L, 185.5, 512.0, 26.0, dosel_w=11.0)
    santo(L, 334.5, 512.0, 26.0, dosel_w=11.0)
    L.linea((x0, ZOCALO), (xa, ZOCALO), peso="d")
    L.linea((xb, ZOCALO), (x1, ZOCALO), peso="d")
    # sombra arrojada por la torre izquierda sobre el contrafuerte
    L.rayado(rect(x0 + 0.6, COR_C + 6, CONT_I[1] - 0.6, ZOCALO - 1), ang=68, sep=3.0, margen=(0.2, 0.9))


def edificio_izq(L):
    """Casa colindante a la izquierda, sugerida y desvaneciéndose hacia el borde."""
    rng = L.rng
    with L.detras_de(rect(78.5, 140, 170, 600)):
        L.linea((6.0, 408.0), (84.0, 406.0), peso="d")
        L.linea((12.0, 401.0), (84.0, 400.0), peso="s")
        L.linea((22.0, 391.0), (84.0, 388.0), peso="d")
        L.rayado([(8, 408.5), (84, 406.5), (84, 412), (8, 413.5)], ang=62, sep=2.5, margen=(0.3, 1.2),
                 largo=lambda fx, fy: 0.15 + fx)
        for x, y0, y1 in ((26.0, 428.0, 456.0), (58.0, 428.0, 456.0), (58.0, 492.0, 520.0)):
            L.linea((x - 7, y1), (x - 7, y0), (x + 7, y0), (x + 7, y1), peso="d")
            L.linea((x - 9, y1), (x + 9, y1), peso="d")
            L.linea((x, y0 + 1), (x, y1 - 1), peso="s")
            L.rayado(rect(x - 6.5, y0 + 0.5, x - 0.8, y1 - 0.5), ang=70, sep=2.2, margen=(0.3, 1.0))
        # portal
        L.linea((18.0, BASE + 1), (18.0, 500.0), (36.0, 500.0), (36.0, BASE + 1), peso="d")
        L.rayado(rect(18.5, 500.5, 35.5, BASE), ang=76, sep=2.1, margen=(0.3, 0.9),
                 largo=lambda fx, fy: 1.0 if fx < 0.7 else 0.3)
        L.linea((10.0, 562.0), (82.0, 562.0), peso="s")


def arbol_der(L):
    poly = copa(L, 474.0, 488.0, 42.0, 58.0, n=14, peso="d", abultado=0.3, abierto=1, fase=15)
    festones_interiores(L, 478.0, 494.0, 32.0, 42.0, n=5, peso="s", lado=0.6)
    L.curva([(462.0, 593.0), (464.0, 572.0), (465.5, 545.0)], peso="d")
    L.curva([(476.0, 593.0), (474.0, 572.0), (474.5, 547.0)], peso="d")
    L.curva([(465.5, 552.0), (458.0, 537.0), (450.0, 527.0)], peso="s")
    L.curva([(474.0, 550.0), (483.0, 532.0), (492.0, 522.0)], peso="s")
    L.curva([(469.5, 549.0), (470.0, 530.0), (468.0, 516.0)], peso="s")
    L.rayado([(470.0, 590), (475.5, 590), (474.5, 550), (470.0, 552)], ang=80, sep=1.6, margen=(0.2, 0.4))
    L.rayado(poly, ang=52, sep=2.5, margen=(0.8, 2.2),
             largo=lambda fx, fy: max(0.0, (fx - 0.42) * 1.9) * (0.4 + fy), ancla="b")
    tronco_poly = [(460, 595), (478, 595), (478, 544), (460, 544)]
    return poly, tronco_poly


def gradas_y_suelo(L):
    rng = L.rng
    L.linea((150.0, BASE + 1), (370.0, BASE + 1), peso="c")
    L.linea((141.0, 585.5), (379.0, 585.0), peso="d")
    L.linea((133.0, 592.0), (388.0, 591.5), peso="d")
    L.rayado(rect(150, 579.5, 370, 584.5), ang=0, sep=2.4, margen=(2.0, 30.0), prob=0.5, var=0.1)
    L.linea((62.0, BASE + 1), (150.0, BASE + 1), peso="c")
    L.linea((370.0, BASE + 1), (442.0, BASE + 1), peso="c")
    with L.textura("s"):
        for y, a, b in ((599.0, 70, 450), (606.0, 120, 420), (613.0, 190, 340)):
            x = a + rng.uniform(0, 14)
            while x < b:
                lg = rng.uniform(14, 46)
                if rng.random() < 0.8:
                    L.raya((x, y + rng.uniform(-0.8, 0.8)), (min(b, x + lg), y + rng.uniform(-0.8, 0.8)),
                           curv=0.4)
                x += lg + rng.uniform(5, 14)


def dibujar(semilla=1506):
    L = Lienzo(W, H, semilla=semilla)
    copa_poly, tronco_poly = arbol_der(L)
    with L.detras_de(copa_poly, tronco_poly):
        torre(L, TI[0], TI[1], TOP_I, -1)
        torre(L, TD[0], TD[1], TOP_D, 1, reloj=True)
        campanario(L, TI[0] + 11.5, TI[1] - 11.5, TOP_I - 6.5, 98.0, -1)
        campanario(L, TD[0] + 11.5, TD[1] - 11.5, TOP_D - 6.5, 95.0, 1)
        cuerpo_central(L)
        gradas_y_suelo(L)
    edificio_izq(L)
    # aguadas (con desregistro de 2-4 unidades)
    centro = [(TI[1], ZOCALO), (TI[1], COR_C), (171, COR_C - 4.5), APEX, (349, COR_C - 4.5),
              (TD[0], COR_C), (TD[0], ZOCALO)]
    L.aguada(centro, OCRE, op=0.34, dx=3, dy=2.2)
    L.aguada(rect(TI[0], TOP_I, TI[1], ZOCALO), OCRE, op=0.14, dx=2.6, dy=2.5)
    L.aguada(rect(TD[0], TOP_D, TD[1], ZOCALO), OCRE, op=0.14, dx=3.2, dy=1.8)
    L.aguada(rect(TI[0] + 11, 92, TI[1] - 11, TOP_I - 6), OCRE, op=0.14, dx=2.5, dy=2.5, amp=1.4)
    L.aguada(rect(TD[0] + 11, 89, TD[1] - 11, TOP_D - 6), OCRE, op=0.14, dx=2.5, dy=2.5, amp=1.4)
    izq, der = conopial_pts(CX, 66.0, 478.0, 58.0, n=10)
    L.aguada(izq + der[1:] + [(326, ZOCALO), (194, ZOCALO)], OCRE, op=0.2, dx=2.5, dy=3, amp=1.6)
    L.aguada(rect(163, 182, 177, ZOCALO), OCRE, op=0.2, dx=2, dy=2, amp=1.2)
    L.aguada([(240, ZOCALO), (240, 544), (260, 516), (280, 544), (280, ZOCALO)], TERRACOTA, op=0.3,
             dx=2.4, dy=2.0, amp=1.0, paso=8)
    L.aguada(copa_poly, OLIVA, op=0.32, dx=3.5, dy=2.5, amp=3.0)
    L.aguada([(60, 586), (460, 586), (452, 612), (80, 612)], OCRE, op=0.13, dx=0, dy=1, amp=3.5)
    L.aguada([(22, 389), (84, 386), (84, 401), (14, 403)], TERRACOTA, op=0.18, dx=2, dy=2, amp=1.2, paso=9)
    return L


TITULO = "Iglesia de San Pablo, Valladolid: dibujo a pluma"
