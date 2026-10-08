"""
motivos.py · piezas de dibujo reutilizables (arquitectura, árboles, figuras).

Todas las funciones reciben un Lienzo (pluma.py) y dibujan sobre él.
Devuelven, cuando tiene sentido, el polígono ideal de la pieza para usarlo
como oclusor (lo que esté detrás se interrumpe).
"""
import math
from pluma import arco_pts, lerp, unit, dist, rect, catmull_denso


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def arco_3p(a, m, b, n=6):
    """Arco de circunferencia que pasa por a, m, b (m = punto medio del arco)."""
    ax, ay = a
    bx, by = b
    mx, my = m
    d = 2 * (ax * (my - by) + mx * (by - ay) + bx * (ay - my))
    if abs(d) < 1e-9:
        return [a, m, b]
    ux = ((ax * ax + ay * ay) * (my - by) + (mx * mx + my * my) * (by - ay) + (bx * bx + by * by) * (ay - my)) / d
    uy = ((ax * ax + ay * ay) * (bx - mx) + (mx * mx + my * my) * (ax - bx) + (bx * bx + by * by) * (mx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.atan2(ay - uy, ax - ux)
    am = math.atan2(my - uy, mx - ux)
    a1 = math.atan2(by - uy, bx - ux)

    def norm(x):
        while x < 0:
            x += math.tau
        while x >= math.tau:
            x -= math.tau
        return x
    # recorrer de a0 a a1 pasando por am
    d1 = norm(a1 - a0)
    dm = norm(am - a0)
    if dm > d1:
        d1 = d1 - math.tau
    return [(ux + r * math.cos(a0 + d1 * i / n), uy + r * math.sin(a0 + d1 * i / n)) for i in range(n + 1)]


# ---------------------------------------------------------------- arcos
def apuntado_pts(x0, x1, ys, k=0.9, n=10):
    """Arco apuntado entre x0 y x1 con arranque en ys. k = radio/luz (0.5 = medio punto)."""
    luz = x1 - x0
    r = max(luz * k, luz / 2 + 0.01)
    cx_i = x0 + r
    xm = (x0 + x1) / 2
    ang = math.degrees(math.acos((xm - cx_i) / r))
    izq = arco_pts(cx_i, ys, r, r, 180, ang, n=n)
    cx_d = x1 - r
    der = arco_pts(cx_d, ys, r, r, 180 - ang, 0, n=n)
    return izq, der


def apuntado(L, x0, x1, ys, k=0.9, peso="d", jambas=None, **kw):
    """Arco apuntado en un solo trazo (con jambas opcionales hasta y=jambas)."""
    izq, der = apuntado_pts(x0, x1, ys, k)
    pts = izq + der[1:]
    if jambas is not None:
        pts = [(x0, jambas)] + pts + [(x1, jambas)]
    L.trazo(pts, peso=peso, suave=False, **kw)
    return pts


def conopial_pts(cx, xh, ys, h, hombro=0.9, punta=0.62, n=16):
    """Arco conopial (ogee): mitades izquierda y derecha.

    Sube vertical desde (cx-xh, ys), hace hombro convexo, cambia de curvatura y
    remata en punta vertical en (cx, ys-h)."""
    P0 = (cx - xh, ys)
    P1 = (cx - xh, ys - h * hombro)
    P2 = (cx, ys - h * (1 - punta))
    P3 = (cx, ys - h)
    izq = [_bez(P0, P1, P2, P3, i / n) for i in range(n + 1)]
    der = [(2 * cx - x, y) for (x, y) in reversed(izq)]
    return izq, der


def cresteria(L, pts, cada=7.0, alto=3.6, lado=1, peso="s", desde=0.0, hasta=1.0):
    """Cresterías (ganchos/cardinas) como UNA línea ondulada que se enrosca hacia delante.

    pts: curva base (de abajo hacia el remate). lado: 1 = a la izquierda del avance."""
    rng = L.rng
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + dist(pts[i - 1], pts[i]))
    T = cum[-1]

    def en(s):
        for i in range(1, len(pts)):
            if cum[i] >= s:
                t = (s - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
                p = lerp(pts[i - 1], pts[i], t)
                tu = unit((pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
                return p, tu
        tu = unit((pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]))
        return pts[-1], tu
    s = T * desde + cada * rng.uniform(0.3, 0.6)
    fin = T * hasta - cada * 0.3
    out = []
    while s < fin:
        p, tu = en(s)
        nrm = (tu[1] * lado, -tu[0] * lado)
        a = alto * rng.uniform(0.8, 1.15)
        b = (p[0] + nrm[0] * 0.6, p[1] + nrm[1] * 0.6)
        t1 = (p[0] + nrm[0] * a * 0.95 + tu[0] * cada * 0.22, p[1] + nrm[1] * a * 0.95 + tu[1] * cada * 0.22)
        t2 = (p[0] + nrm[0] * a * 0.75 + tu[0] * cada * 0.62, p[1] + nrm[1] * a * 0.75 + tu[1] * cada * 0.62)
        out += [b, t1, t2]
        s += cada * rng.uniform(0.88, 1.12)
    if len(out) >= 3:
        p, tu = en(min(s, T))
        out.append(p)
        L.trazo(out, peso=peso, suave=True, pasado=(0, 0.3), amp=0.12, tramo=6.0, hueco=(0, 1e9))


# ------------------------------------------------------------- ornamento
def pinaculo(L, x, yb, yt, w, peso="d", ganchos_n=1, bola=True):
    """Pináculo gótico: fuste y aguja en un trazo (con ganchillos en el perfil), imposta y florón."""
    rng = L.rng
    ym = yb - (yb - yt) * rng.uniform(0.38, 0.48)
    hx = w / 2
    izq = [(x - hx, yb), (x - hx, ym)]
    der = [(x + hx, ym), (x + hx, yb)]
    sube = []
    n = max(1, ganchos_n)
    for k in range(1, n + 1) if ganchos_n else []:
        t = k / (n + 1)
        py = ym - (ym - yt) * t
        px = hx * (1 - t)
        sube.append((x - px, py + 0.8))
        sube.append((x - px - 1.7, py - 0.6))
        sube.append((x - px * 0.85, py - 1.4))
    baja = [(2 * x - p[0], p[1]) for p in reversed(sube)]
    L.linea(*(izq + sube + [(x + rng.uniform(-0.3, 0.3), yt)] + baja + der), peso=peso, pasado=(-0.3, 0.6))
    L.linea((x - hx - 1.2, ym + 0.3), (x + hx + 1.2, ym + 0.3), peso="s", pasado=(-0.2, 0.4))
    if bola:
        L.punto(x, yt - 1.2, 0.9, peso="s")


def estatua(L, x, yb, h, peso="s", gira=0.0, sentada=False, nimbo=False):
    """Estatua diminuta: cabeza redonda y túnica (2 trazos; 3 con nimbo)."""
    rng = L.rng
    r = h * (0.095 if not sentada else 0.12)
    hx = x + gira * 0.5
    hy = yb - h + r
    L.circulo(hx, hy, r, peso=peso, solape=rng.uniform(10, 40))
    if nimbo:
        L.trazo(arco_pts(hx, hy - r * 0.2, r * 2.0, r * 2.0, rng.uniform(-30, -10), rng.uniform(190, 210), n=8),
                peso="s", suave=True)
    sh = h * (0.16 if not sentada else 0.2)
    y0 = hy + r + 0.6
    if sentada:
        pts = [(hx - sh * 0.75, y0), (x - sh * 1.15, y0 + h * 0.18), (x - sh * 1.2, yb - h * 0.38),
               (x - sh * 1.75, yb - h * 0.3), (x - sh * 1.5, yb), (x + sh * 1.5, yb),
               (x + sh * 1.75, yb - h * 0.3), (x + sh * 1.2, yb - h * 0.38), (x + sh * 1.15, y0 + h * 0.18),
               (hx + sh * 0.75, y0)]
    else:
        pts = [(hx - sh * 0.8, y0), (x - sh * 1.05 + gira * 0.3, yb - h * 0.55), (x - sh * 0.95 + gira, yb - h * 0.25),
               (x - sh * 1.3, yb), (x + sh * 1.3, yb), (x + sh * 0.95 + gira, yb - h * 0.25),
               (x + sh * 1.05 + gira * 0.3, yb - h * 0.55), (hx + sh * 0.8, y0)]
    L.trazo(pts, peso=peso, suave=False, pasado=(-0.3, 0.4))


def santo(L, x, yb, h, peso="d", dosel_w=None, gira=None, sombra=True):
    """Santo sobre peana bajo doselete (como en las portadas isabelinas)."""
    rng = L.rng
    g = rng.uniform(-1.0, 1.0) if gira is None else gira
    w = dosel_w or h * 0.5
    # peana
    L.linea((x - w * 0.5, yb), (x + w * 0.5, yb), (x + w * 0.32, yb + 3.2), (x - w * 0.32, yb + 3.2),
            (x - w * 0.45, yb + 0.4), peso="s", pasado=(-0.2, 0.4))
    estatua(L, x, yb - 0.4, h, peso=peso, gira=g)
    dosel(L, x, yb - h - 2.5, w)
    if sombra:
        # sombra arrojada por la figura en el muro (a la derecha)
        sh = h * 0.16
        poly = [(x + sh * 0.9, yb - h * 0.8), (x + sh * 2.3, yb - h * 0.72), (x + sh * 2.6, yb - 1), (x + sh * 1.3, yb - 1)]
        L.rayado(poly, ang=64, sep=1.9, margen=(0.2, 0.6), minimo=0.8, ang_var=4)


def dosel(L, x, y, w, peso="s"):
    """Doselete: tejadillo apuntado con florón, en un solo trazo."""
    rng = L.rng
    h = w * rng.uniform(0.6, 0.75)
    r = 0.9
    pts = [(x - w / 2 - 0.8, y), (x - w / 2, y - 1.6), (x - 0.4, y - h + 0.3), (x - r, y - h - 1.0),
           (x, y - h - 2.4), (x + r, y - h - 1.0), (x + 0.4, y - h + 0.3), (x + w / 2, y - 1.6), (x + w / 2 + 0.8, y)]
    L.trazo(pts, peso=peso, suave=False, pasado=(-0.2, 0.6))


def nicho(L, x, yb, w, h, peso="s", figura=True, dosel_w=None, sombra=True, apuntado_k=0.75,
          ped=True, peso_fig="d"):
    """Hornacina (arco apuntado) con estatua y doselete opcional. Devuelve el polígono."""
    rng = L.rng
    ys = yb - h + w * 0.55
    izq, der = apuntado_pts(x - w / 2, x + w / 2, ys, k=apuntado_k, n=6)
    pts = [(x - w / 2, yb)] + izq + der[1:] + [(x + w / 2, yb)]
    L.trazo(pts, peso=peso, suave=False, pasado=(-0.4, 0.8))
    if sombra:
        top = izq[2:] + der[1:-2]
        poly = [(x - w / 2, ys + 3)] + izq + der[1:] + [(x + w / 2, ys + 3)]
        L.rayado(poly, ang=64, sep=2.2, margen=(0.3, 0.9), minimo=1.0, ang_var=4,
                 largo=lambda fx, fy: 1.0 if fx < 0.55 else 0.35)
    if ped:
        L.linea((x - w / 2 - 1.2, yb), (x + w / 2 + 1.2, yb), peso="s", pasado=(-0.2, 0.5))
    if figura:
        estatua(L, x, yb - 0.8, h * rng.uniform(0.66, 0.74), peso=peso_fig, gira=rng.uniform(-1.0, 1.0))
    if dosel_w:
        dosel(L, x, yb - h - 1.0, dosel_w)
    return pts


def escudo(L, cx, cy, w, h, peso="d", cimera=True, lambrequin=True, cuartel=True):
    """Escudo de armas: campo, cuartelado, corona y lambrequines."""
    rng = L.rng
    x0, x1 = cx - w / 2, cx + w / 2
    yt, yb = cy - h / 2, cy + h / 2
    ym = yb - w / 2
    fondo = arco_pts(cx, ym, w / 2, w / 2, 0, -180, n=10)
    pts = [(x0, yt), (x1, yt)] + [(x1, ym)] + fondo[1:-1] + [(x0, ym), (x0, yt)]
    L.trazo(pts, peso=peso, suave=False)
    if cuartel:
        with L.textura("s"):
            L.raya((cx + rng.uniform(-0.4, 0.4), yt + 1.0), (cx, yb - 1.2), curv=0.2)
            L.raya((x0 + 1, cy - h * 0.08), (x1 - 1, cy - h * 0.08), curv=0.2)
            for qx, qy in ((cx + w * 0.24, cy - h * 0.28), (cx - w * 0.24, cy + h * 0.14)):
                L.raya((qx - 1.8, qy), (qx + 1.8, qy), curv=0)
                L.raya((qx, qy - 1.8), (qx, qy + 1.8), curv=0)
        for qx, qy in ((cx - w * 0.24, cy - h * 0.28), (cx + w * 0.24, cy + h * 0.14)):
            L.curva([(qx - 1.8, qy + 1.6), (qx - 0.5, qy - 1.6), (qx + 1.2, qy + 0.2), (qx + 1.9, qy + 1.8)],
                    peso="s", amp=0.1)
    if cimera:
        cw = w * 0.62
        yc = yt - 1.5
        L.trazo([(cx - cw / 2, yc), (cx - cw / 2 - 0.6, yc - 4.2), (cx - cw / 4, yc - 2.2), (cx, yc - 5.4),
                 (cx + cw / 4, yc - 2.2), (cx + cw / 2 + 0.6, yc - 4.2), (cx + cw / 2, yc), (cx - cw / 2, yc)],
                peso="s", suave=False, pasado=(-0.2, 0.3))
    if lambrequin:
        for s in (-1, 1):
            bx = cx + s * (w / 2 + 0.8)
            L.curva([(cx + s * w * 0.3, yt - 1.0), (bx + s * 2.5, yt + 1.5), (bx + s * 1.2, yt + h * 0.3),
                     (bx + s * 3.8, yt + h * 0.45), (bx + s * 2.0, yt + h * 0.7)], peso="s", amp=0.15)
    return pts


def roseton(L, cx, cy, r, radios=12):
    """Rosetón: anillos, cubo y radios con lóbulos (los lóbulos en una sola línea festoneada)."""
    rng = L.rng
    L.circulo(cx, cy, r, peso="d")
    L.circulo(cx, cy, r * 0.84, peso="s")
    L.circulo(cx, cy, r * 0.24, peso="s")
    a0 = rng.uniform(0, 30)
    with L.textura("s"):
        for k in range(radios):
            a = math.radians(a0 + k * 360 / radios + rng.uniform(-2, 2))
            L.raya((cx + r * 0.27 * math.cos(a), cy - r * 0.27 * math.sin(a)),
                   (cx + r * 0.6 * math.cos(a), cy - r * 0.6 * math.sin(a)), curv=0.1)
    # lóbulos: una guirnalda de arquillos entre radios, cerca del anillo interior
    pts = []
    for k in range(radios + 1):
        a1 = math.radians(a0 + k * 360 / radios)
        am = math.radians(a0 + (k + 0.5) * 360 / radios)
        pts.append((cx + r * 0.6 * math.cos(a1), cy - r * 0.6 * math.sin(a1)))
        pts.append((cx + r * 0.8 * math.cos(am), cy - r * 0.8 * math.sin(am)))
    L.trazo(pts[:-1], peso="s", suave=True, tramo=5.0, amp=0.1)


# ------------------------------------------------------------- vegetación
def copa(L, cx, cy, rx, ry, n=11, peso="d", irregular=0.12, abultado=0.3, abierto=0, fase=None,
         aplastar_base=0.0, dibujar=True):
    """Copa de árbol a festones redondos. Devuelve el polígono ideal (para ocluir)."""
    rng = L.rng
    f0 = rng.uniform(0, 360) if fase is None else fase
    ang = sorted((f0 + 360 * i / n + rng.uniform(-0.25, 0.25) * 360 / n) % 360 for i in range(n))
    base = []
    for a in ang:
        k = 1 + rng.uniform(-irregular, irregular)
        ar = math.radians(a)
        y = cy - ry * k * math.sin(ar)
        if aplastar_base and y > cy:
            y = cy + (y - cy) * (1 - aplastar_base)
        base.append((cx + rx * k * math.cos(ar), y))
    poly = []
    festones = []
    for i in range(n):
        a, b = base[i], base[(i + 1) % n]
        m = lerp(a, b, 0.5)
        ch = dist(a, b)
        out = unit((m[0] - cx, m[1] - cy))
        h = ch * abultado * rng.uniform(0.75, 1.25)
        pts = arco_3p(a, (m[0] + out[0] * h, m[1] + out[1] * h), b, n=6)
        festones.append(pts)
        poly += pts[:-1]
    if dibujar:
        saltar = set(rng.sample(range(n), abierto)) if abierto else set()
        actual = []
        grupos = []
        for i in range(n):
            if i in saltar:
                if actual:
                    grupos.append(actual)
                actual = []
                continue
            actual += festones[i] if not actual else festones[i][1:]
        if actual:
            grupos.append(actual)
        for g in grupos:
            L.trazo(g, peso=peso, suave=False, pasado=(-0.4, 1.0))
    return poly


def festones_interiores(L, cx, cy, rx, ry, n=5, peso="s", lado=0.4):
    """Arquitos dentro de la copa que sugieren masas de hojas (más en el lado de sombra)."""
    rng = L.rng
    for _ in range(n):
        ax = cx + rx * rng.uniform(-0.5, 0.55) + rx * lado * 0.3
        ay = cy + ry * rng.uniform(-0.4, 0.5)
        w = rx * rng.uniform(0.16, 0.26)
        a0 = rng.uniform(165, 200)
        L.trazo(arco_pts(ax, ay, w, w * 0.85, a0, a0 - rng.uniform(120, 160), n=6), peso=peso, suave=True)
