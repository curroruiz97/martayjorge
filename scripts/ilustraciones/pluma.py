"""
pluma.py · motor de «dibujo a pluma» para las ilustraciones de Marta y Jorge.

Convierte geometría ideal (rectas, polilíneas, curvas, círculos, zonas a rayar)
en trazos SVG con aspecto de dibujo a mano:
  · temblor suave (ruido de baja frecuencia + leve curvatura en las rectas largas),
  · pequeños «pasados» o quedarse corto en los extremos,
  · huecos intencionados en trazos largos,
  · grosor distinto en cada trazo dentro de su familia (contorno/detalle/sombra),
  · sombreado a rayitas con separación, longitud y ángulo irregulares,
  · recorte por oclusión (lo que queda detrás se interrumpe, con un hueco).

Cada trazo sale como su propio <path class="l" pathLength="1"> para poder
animar el efecto «se dibuja solo» con stroke-dasharray / stroke-dashoffset.
Todo es determinista (semilla fija): ejecutar de nuevo da el mismo SVG.

Solo usa la biblioteca estándar de Python 3.
"""
import math
import random
from contextlib import contextmanager

TINTA = "#4b3c37"          # marrón grisáceo oscuro (el mismo que --tinta en base.css)
ROJO = "#a3121d"           # rojo de la tinta de la web (nombres, títulos, ruta, favicon)
OCRE = "#c3a063"
TERRACOTA = "#a4563a"
OLIVA = "#6c7550"

TAU = math.tau

# ----------------------------------------------------------------------------
# números y datos de trazado compactos
# ----------------------------------------------------------------------------

def fnum(v, dec=1):
    """Número con 1 decimal como máximo (o entero si dec=0) y sin ceros superfluos (.5, -.5, 12)."""
    v = round(v + 0.0, dec)
    if v == 0:
        return "0"
    if dec == 0:
        return "%d" % v
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


class Datos:
    """Construye un atributo d con coordenadas relativas redondeadas a 1 decimal.

    El punto actual se guarda ya redondeado, así el error no se acumula."""

    def __init__(self, dec=1):
        self.tok = []          # trozos de texto
        self.cmd = None        # último comando escrito
        self.prev = ""         # último número escrito
        self.cur = (0.0, 0.0)
        self.dec = dec         # decimales (1, o 0 para texturas y aguadas)

    def _nums(self, cmd, nums):
        strs = [fnum(n, self.dec) for n in nums]
        if cmd != self.cmd or cmd in "Mm":
            self.tok.append(cmd)
            self.prev = ""
            self.cmd = cmd
        for s in strs:
            if self.prev == "" or s[0] == "-" or (s[0] == "." and "." in self.prev):
                self.tok.append(s)
            else:
                self.tok.append(" " + s)
            self.prev = s

    def _r(self, p):
        return (round(p[0], self.dec), round(p[1], self.dec))

    def M(self, p):
        p = self._r(p)
        self._nums("M", p)
        self.cur = p
        # tras M los números implícitos serían «L»; forzamos comando nuevo
        self.cmd = "M"

    def _d(self, p):
        return (round(p[0] - self.cur[0], self.dec), round(p[1] - self.cur[1], self.dec))

    def m(self, p):
        """Movimiento relativo (nuevo subtrazo dentro del mismo path)."""
        d = self._d(p)
        self._nums("m", d)
        self.cur = (round(self.cur[0] + d[0], self.dec), round(self.cur[1] + d[1], self.dec))
        self.cmd = "m"

    def l(self, p):
        d = self._d(p)
        self._nums("l", d)
        self.cur = (round(self.cur[0] + d[0], self.dec), round(self.cur[1] + d[1], self.dec))

    def c(self, c1, c2, p):
        a, b, d = self._d(c1), self._d(c2), self._d(p)
        self._nums("c", a + b + d)
        self.cur = (round(self.cur[0] + d[0], self.dec), round(self.cur[1] + d[1], self.dec))

    def s(self, c2, p):
        b, d = self._d(c2), self._d(p)
        self._nums("s", b + d)
        self.cur = (round(self.cur[0] + d[0], self.dec), round(self.cur[1] + d[1], self.dec))

    def q(self, c1, p):
        a, d = self._d(c1), self._d(p)
        self._nums("q", a + d)
        self.cur = (round(self.cur[0] + d[0], self.dec), round(self.cur[1] + d[1], self.dec))

    def z(self):
        self.tok.append("z")
        self.cmd = "z"
        self.prev = ""

    def texto(self):
        return "".join(self.tok)


# ----------------------------------------------------------------------------
# geometría básica
# ----------------------------------------------------------------------------

def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def longitud(pts):
    return sum(dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def unit(v):
    m = math.hypot(v[0], v[1])
    if m < 1e-9:
        return (1.0, 0.0)
    return (v[0] / m, v[1] / m)


def dentro(p, poly):
    """Punto en polígono (par-impar)."""
    x, y = p
    ins = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xc = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < xc:
                ins = not ins
        j = i
    return ins


def caja(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def catmull_denso(pts, cerrado=False, paso=2.0):
    """Muestrea densamente una Catmull-Rom uniforme que pasa por pts."""
    n = len(pts)
    if n < 2:
        return list(pts)
    if cerrado:
        P = [pts[-1]] + list(pts) + [pts[0], pts[1]]
        nseg = n
    else:
        P = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + list(pts) + \
            [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
        nseg = n - 1
    out = []
    for i in range(nseg):
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        L = dist(p1, p2)
        k = max(2, int(math.ceil(L / paso)))
        for j in range(k):
            t = j / k
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[0] if cerrado else pts[-1])
    return out


def poli_denso(pts, paso=2.0):
    """Densifica una polilínea; devuelve (puntos, índices de esquina)."""
    out = [pts[0]]
    esquinas = set()
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = dist(a, b)
        k = max(1, int(math.ceil(L / paso)))
        for j in range(1, k + 1):
            out.append(lerp(a, b, j / k))
        if i < len(pts) - 2:
            # ¿hay giro apreciable en el vértice b?
            c = pts[i + 2]
            u, v = unit((b[0] - a[0], b[1] - a[1])), unit((c[0] - b[0], c[1] - b[1]))
            if u[0] * v[0] + u[1] * v[1] < math.cos(math.radians(28)):
                esquinas.add(len(out) - 1)
    return out, esquinas


def arco_pts(cx, cy, rx, ry, a0, a1, n=None, paso=3.0):
    """Puntos de un arco de elipse. Ángulos en grados, 0 = derecha, 90 = arriba."""
    if n is None:
        L = abs(math.radians(a1 - a0)) * (rx + ry) / 2
        n = max(3, int(math.ceil(L / paso)))
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + rx * math.cos(a), cy - ry * math.sin(a)))
    return out


def desplaza(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def ondas(rng, amp, l1=(60, 130), l2=(16, 32), l3=(6, 11)):
    """Ruido 1D suave (suma de senos con fase aleatoria) en función de la longitud."""
    L1, L2, L3 = rng.uniform(*l1), rng.uniform(*l2), rng.uniform(*l3)
    f1, f2, f3 = rng.uniform(0, TAU), rng.uniform(0, TAU), rng.uniform(0, TAU)
    a1, a2, a3 = amp * 0.72, amp * 0.33, amp * 0.14

    def f(s):
        return (a1 * math.sin(TAU * s / L1 + f1) + a2 * math.sin(TAU * s / L2 + f2) +
                a3 * math.sin(TAU * s / L3 + f3))
    return f


# ----------------------------------------------------------------------------
# el lienzo
# ----------------------------------------------------------------------------

class Lienzo:
    # familia: (mín, máx, paso de cuantización)
    PESOS = {"c": (2.2, 2.4, 0.2), "d": (1.2, 1.4, 0.2), "s": (0.8, 1.0, 0.1)}
    # temblor base, longitud de tramo entre puntos de control
    TEMBLOR = {"c": 0.62, "d": 0.42, "s": 0.3}
    TRAMO = {"c": 34.0, "d": 22.0, "s": 30.0}
    # pasado en cada extremo: (mín, máx); negativo = se queda corto
    PASADO = {"c": (-0.9, 2.8), "d": (-0.7, 1.6), "s": (-0.4, 0.6)}
    HUECO = {"c": (0.24, 95.0), "d": (0.12, 70.0), "s": (0.0, 1e9)}

    def __init__(self, ancho, alto, semilla=1, temblor=1.0, escala_pasado=1.0):
        self.w, self.h = ancho, alto
        self.rng = random.Random(semilla)
        self.temblor = temblor
        self.escala_pasado = escala_pasado
        self.trazos = []        # (familia, ancho, n, d)
        self.aguadas = []       # (color, opacidad, d)
        self.clips = []         # pila de oclusores activos
        self.n = 0
        self.extra_linea = []   # elementos extra (p. ej. puntos rellenos) dentro de .linea
        self._grupo = None      # textura en curso (varios subtrazos en un path)

    # ------------------------------------------------------------ texturas
    @contextmanager
    def textura(self, peso="s", ancho=None):
        """Agrupa rayas cortas (rayado, sillería, tejas...) en UN path con subtrazos.

        Al animar con pathLength=1, cada subtrazo arranca a la vez (el patrón de
        guiones se reinicia en cada subtrazo), así que el rayado «aparece» de golpe
        mientras las líneas se dibujan: queda natural y ahorra muchos bytes."""
        if self._grupo is not None:          # ya estamos dentro de otra textura
            yield
            return
        self._grupo = {"peso": peso, "d": Datos(dec=0), "k": 0, "ancho": ancho}
        try:
            yield
        finally:
            g, self._grupo = self._grupo, None
            if g["k"]:
                self.n += 1
                self.trazos.append((g["peso"], self._ancho(g["peso"], g["ancho"]), self.n,
                                    g["d"].texto()))

    # ------------------------------------------------------------- oclusión
    @contextmanager
    def detras_de(self, *polys):
        """Todo lo que se dibuje dentro queda recortado por estos polígonos."""
        prep = [(caja(p), p) for p in polys if p]
        self.clips.append(prep)
        try:
            yield
        finally:
            self.clips.pop()

    def _oculto(self, p):
        for capa in self.clips:
            for (x0, y0, x1, y1), poly in capa:
                if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and dentro(p, poly):
                    return True
        return False

    def _recortar(self, denso, esquinas):
        """Divide la polilínea densa en tramos visibles.

        Devuelve [(puntos, esquinas, extremo_ini_recortado, extremo_fin_recortado)]."""
        if not self.clips:
            return [(denso, esquinas, False, False)]
        vis = [not self._oculto(p) for p in denso]
        if all(vis):
            return [(denso, esquinas, False, False)]
        tramos = []
        i, n = 0, len(denso)
        while i < n:
            if not vis[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and vis[j + 1]:
                j += 1
            pts = denso[i:j + 1]
            ini_rec = i > 0
            fin_rec = j < n - 1
            # afinar el borde por bisección
            if ini_rec:
                a, b = denso[i - 1], denso[i]
                for _ in range(8):
                    m = lerp(a, b, 0.5)
                    if self._oculto(m):
                        a = m
                    else:
                        b = m
                pts = [b] + pts
            if fin_rec:
                a, b = denso[j], denso[j + 1]
                for _ in range(8):
                    m = lerp(a, b, 0.5)
                    if self._oculto(m):
                        b = m
                    else:
                        a = m
                pts = pts + [a]
            off = i - (1 if ini_rec else 0)
            esq = {k - off for k in esquinas if i <= k <= j}
            tramos.append((pts, esq, ini_rec, fin_rec))
            i = j + 1
        return tramos

    # --------------------------------------------------------------- grosor
    def _ancho(self, fam, ancho=None):
        if ancho is not None:
            return round(ancho, 1)
        lo, hi, q = self.PESOS[fam]
        k = int(round((hi - lo) / q))
        return round(lo + q * self.rng.randint(0, k), 1)

    # ------------------------------------------------------- trazo genérico
    def trazo(self, pts, peso="d", suave=False, cerrado=False, amp=None,
              pasado=None, hueco=None, tramo=None, ancho=None, curvar=1.0,
              recortar=True, giro=38.0):
        """Dibuja una línea a mano alzada que sigue pts.

        suave=True: pts son puntos de paso de una curva (Catmull-Rom).
        suave=False: polilínea; los vértices con giro > 28° se mantienen como esquinas.
        """
        if len(pts) < 2:
            return
        if suave:
            denso = catmull_denso(pts, cerrado)
            esquinas = set()
        else:
            P = list(pts) + ([pts[0]] if cerrado else [])
            denso, esquinas = poli_denso(P)
        tramos = self._recortar(denso, esquinas) if recortar else [(denso, esquinas, False, False)]
        for t_pts, t_esq, r0, r1 in tramos:
            if longitud(t_pts) < 1.2:
                continue
            self._emitir(t_pts, t_esq, peso, amp, pasado, hueco, tramo, ancho,
                         r0, r1, curvar, cerrado and not self.clips, giro)

    def _emitir(self, pts, esquinas, fam, amp, pasado, hueco, tramo, ancho,
                r0, r1, curvar, cerrado, giro=38.0):
        rng = self.rng
        L = longitud(pts)
        # --- extremos: pasado o quedarse corto
        lo, hi = pasado if pasado is not None else self.PASADO[fam]
        lo *= self.escala_pasado
        hi *= self.escala_pasado
        e0 = rng.uniform(lo, hi) if not r0 else -rng.uniform(0.8, 2.0)
        e1 = rng.uniform(lo, hi) if not r1 else -rng.uniform(0.8, 2.0)
        if cerrado:
            e0, e1 = rng.uniform(-1.5, 0.5), rng.uniform(0.5, 3.0)
        pts, esquinas = _extender(pts, esquinas, e0, e1)
        L = longitud(pts)
        if L < 1.0:
            return
        # --- hueco intencionado
        piezas = [(pts, esquinas)]
        p_h, l_min = hueco if hueco is not None else self.HUECO[fam]
        if L > l_min and rng.random() < p_h:
            s_c = rng.uniform(0.3, 0.7) * L
            g = rng.uniform(1.8, 4.2)
            a, ea, b, eb = _cortar(pts, esquinas, s_c - g / 2, s_c + g / 2)
            piezas = [(a, ea), (b, eb)]
        for pz, ez in piezas:
            if longitud(pz) < 1.0:
                continue
            d = self._datos_mano(pz, ez, fam, amp, tramo, curvar, giro)
            self.n += 1
            self.trazos.append((fam, self._ancho(fam, ancho), self.n, d))

    def _datos_mano(self, pts, esquinas, fam, amp, tramo, curvar, giro_max=38.0):
        rng = self.rng
        L = longitud(pts)
        A = (self.TEMBLOR[fam] if amp is None else amp) * self.temblor
        A *= min(1.0, 0.35 + L / 60.0)
        f = ondas(rng, A)
        arco = rng.uniform(-1, 1) * min(L, 260) * 0.0065 * curvar
        # longitudes acumuladas
        cum = [0.0]
        for i in range(len(pts) - 1):
            cum.append(cum[-1] + dist(pts[i], pts[i + 1]))
        tr = tramo or self.TRAMO[fam]
        # elegir índices de control: extremos, esquinas y cada «tr» unidades
        # (más puntos donde la curva gira)
        ctrl = [0]
        giro = 0.0
        ult = 0.0
        for i in range(1, len(pts) - 1):
            u = unit((pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
            v = unit((pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
            if i not in esquinas:
                giro += abs(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))
            if i in esquinas:
                ctrl.append(i)
                ult, giro = cum[i], 0.0
            elif cum[i] - ult >= tr or giro > math.radians(giro_max):
                # no dejar un último tramo diminuto
                if cum[-1] - cum[i] > (cum[i] - ult) * 0.35:
                    ctrl.append(i)
                    ult, giro = cum[i], 0.0
        ctrl.append(len(pts) - 1)
        # desplazar perpendicularmente
        out = []
        for k, i in enumerate(ctrl):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            t = unit((b[0] - a[0], b[1] - a[1]))
            nrm = (-t[1], t[0])
            s = cum[i]
            dd = f(s) + arco * math.sin(math.pi * s / max(L, 1e-6))
            if i in esquinas:
                dd *= 0.35
            out.append((pts[i][0] + nrm[0] * dd, pts[i][1] + nrm[1] * dd))
        esq_ctrl = {k for k, i in enumerate(ctrl) if i in esquinas}
        return trazado(out, esq_ctrl)

    # -------------------------------------------------------- atajos
    def linea(self, *pts, peso="d", **kw):
        self.trazo(list(pts), peso=peso, suave=False, **kw)

    def curva(self, pts, peso="d", **kw):
        self.trazo(list(pts), peso=peso, suave=True, **kw)

    def arco(self, cx, cy, rx, ry, a0, a1, peso="d", **kw):
        self.trazo(arco_pts(cx, cy, rx, ry, a0, a1), peso=peso, suave=True, **kw)

    def circulo(self, cx, cy, r, peso="d", ry=None, ini=None, solape=None, **kw):
        """Círculo a mano: empieza en un ángulo al azar y se solapa (o no cierra) un poco."""
        rng = self.rng
        ry = r if ry is None else ry
        a0 = rng.uniform(0, 360) if ini is None else ini
        sol = rng.uniform(-8, 22) if solape is None else solape
        n = max(8, int(math.ceil(TAU * max(r, ry) / 5)))
        pts = []
        deriva = rng.uniform(-0.05, 0.05)
        tot = 360 + sol
        for i in range(n + 1):
            t = i / n
            a = math.radians(a0 + tot * t)
            k = 1 + deriva * t
            pts.append((cx + r * k * math.cos(a), cy - ry * k * math.sin(a)))
        kw.setdefault("pasado", (0, 0.3))
        if max(r, ry) < 6:
            kw.setdefault("giro", 58.0)
        self.trazo(pts, peso=peso, suave=True, **kw)

    def punto(self, x, y, r=0.9, peso="d"):
        """Puntito de tinta: un círculo diminuto relleno con el propio trazo."""
        rng = self.rng
        pts = [(x + r * math.cos(a), y + r * math.sin(a))
               for a in [rng.uniform(0, 1) + k * 2.2 for k in range(4)]]
        self.trazo(pts, peso=peso, suave=True, pasado=(0, 0), hueco=(0, 1e9), amp=0.05)

    # -------------------------------------------------------------- rayado
    def rayado(self, poly, ang=60.0, sep=4.0, peso="s", margen=(0.3, 2.0),
               var=0.2, curv=0.5, prob=1.0, largo=None, zig=False,
               ang_var=2.5, minimo=1.6, ancla=None):
        """Sombreado a rayitas dentro de un polígono.

        ang: ángulo de las rayas (grados, 0 = horizontal, 90 = vertical, 60 = «/»).
        largo: función (fx, fy) -> factor de longitud 0..1 (fx, fy relativos a la caja).
        ancla: 'a' | 'b' | None. Desde qué extremo se mide el factor de longitud.
        zig: une las rayas en zigzag en un único trazo (rayado rápido).
        """
        rng = self.rng
        a = math.radians(ang)
        u = (math.cos(a), -math.sin(a))
        nv = (math.sin(a), math.cos(a))
        bx0, by0, bx1, by1 = caja(poly)
        bw, bh = max(bx1 - bx0, 1e-6), max(by1 - by0, 1e-6)
        ts = [p[0] * nv[0] + p[1] * nv[1] for p in poly]
        t0, t1 = min(ts), max(ts)
        t = t0 + sep * rng.uniform(0.3, 0.8)
        segs = []
        while t < t1 - 0.3:
            xs = []
            m = len(poly)
            for i in range(m):
                p, q = poly[i], poly[(i + 1) % m]
                tp = p[0] * nv[0] + p[1] * nv[1]
                tq = q[0] * nv[0] + q[1] * nv[1]
                if (tp <= t < tq) or (tq <= t < tp):
                    k = (t - tp) / (tq - tp)
                    X = lerp(p, q, k)
                    xs.append(X[0] * u[0] + X[1] * u[1])
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                s0 = xs[j] + rng.uniform(*margen)
                s1 = xs[j + 1] - rng.uniform(*margen)
                if s1 - s0 < minimo or rng.random() > prob:
                    continue
                A = (nv[0] * t + u[0] * s0, nv[1] * t + u[1] * s0)
                B = (nv[0] * t + u[0] * s1, nv[1] * t + u[1] * s1)
                if largo is not None:
                    M = lerp(A, B, 0.5)
                    fac = largo((M[0] - bx0) / bw, (M[1] - by0) / bh)
                    fac = max(0.0, min(1.0, fac * rng.uniform(0.82, 1.12)))
                    if fac * dist(A, B) < minimo:
                        continue
                    if ancla == "b":
                        A = lerp(B, A, fac)
                    elif ancla == "a":
                        B = lerp(A, B, fac)
                    else:
                        M = lerp(A, B, 0.5)
                        A, B = lerp(M, A, fac), lerp(M, B, fac)
                # pequeño giro de cada raya
                da = math.radians(rng.uniform(-ang_var, ang_var))
                M = lerp(A, B, 0.5)
                A = _rotar(A, M, da)
                B = _rotar(B, M, da)
                segs.append((A, B))
            t += sep * (1 + rng.uniform(-var, var))
        if not segs:
            return
        if zig:
            pts = []
            for k, (A, B) in enumerate(segs):
                pts += [A, B] if k % 2 == 0 else [B, A]
            self.trazo(pts, peso=peso, suave=False, amp=0.25, pasado=(0, 0.3),
                       hueco=(0, 1e9))
            return
        with self.textura(peso):
            for A, B in segs:
                self.raya(A, B, peso=peso, curv=curv)

    def raya(self, A, B, peso="s", curv=0.5, ancho=None):
        """Una rayita casi recta (curva cuadrática leve)."""
        rng = self.rng
        tramos = [(A, B)]
        if self.clips:
            denso, _ = poli_denso([A, B], paso=1.5)
            tr = self._recortar(denso, set())
            tramos = []
            for pts, _e, r0, r1 in tr:
                a, b = pts[0], pts[-1]
                L = dist(a, b)
                if L < 1.2:
                    continue
                tu = unit((b[0] - a[0], b[1] - a[1]))
                if r0:
                    a = (a[0] + tu[0] * 0.9, a[1] + tu[1] * 0.9)
                if r1:
                    b = (b[0] - tu[0] * 0.9, b[1] - tu[1] * 0.9)
                tramos.append((a, b))
        for a, b in tramos:
            L = dist(a, b)
            if L < 1.0:
                continue
            tu = unit((b[0] - a[0], b[1] - a[1]))
            nrm = (-tu[1], tu[0])
            k = rng.uniform(-curv, curv) * min(1.0, L / 14.0)
            M = lerp(a, b, rng.uniform(0.4, 0.6))
            C = (M[0] + nrm[0] * k * 2, M[1] + nrm[1] * k * 2)
            g = self._grupo
            if g is not None:
                d = g["d"]
                if g["k"] == 0:
                    d.M(a)
                else:
                    d.m(a)
                g["k"] += 1
            else:
                d = Datos()
                d.M(a)
            if L < 3.5:
                d.l(b)
            else:
                d.q(C, b)
            if g is None:
                self.n += 1
                self.trazos.append((peso, self._ancho(peso, ancho), self.n, d.texto()))

    # -------------------------------------------------------------- aguada
    def aguada(self, poly, color, op=0.2, dx=3.0, dy=2.0, amp=2.2, paso=13.0,
               suave=False):
        """Mancha de color con borde irregular, desplazada (desregistro)."""
        rng = self.rng
        P = list(poly) + [poly[0]]
        denso, _ = poli_denso(P, paso=paso)
        denso = denso[:-1]
        f = ondas(rng, amp, l1=(40, 90), l2=(12, 24), l3=(5, 9))
        # normal hacia fuera aproximada (signo según orientación)
        area = 0.0
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            area += x0 * y1 - x1 * y0
        sg = 1 if area > 0 else -1
        out = []
        s = 0.0
        for i, p in enumerate(denso):
            a = denso[i - 1]
            b = denso[(i + 1) % len(denso)]
            t = unit((b[0] - a[0], b[1] - a[1]))
            nrm = (t[1] * sg, -t[0] * sg)
            if i:
                s += dist(denso[i - 1], p)
            d = f(s)
            out.append((p[0] + nrm[0] * d + dx, p[1] + nrm[1] * d + dy))
        dd = trazado(out, set(), cerrado=True, dec=0) if suave else _poli_datos(out)
        self.aguadas.append((color, op, dd))

    # ------------------------------------------------------------ salida
    def datos(self):
        """Lista de atributos d en orden de dibujo (para sprites)."""
        return [d for _f, _w, _n, d in sorted(self.trazos, key=lambda t: t[2])]

    def svg(self, titulo=None, con_color=True, op_color=None, attrs=""):
        W, H = self.w, self.h
        o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s"%s>' % (fnum(W), fnum(H), attrs)]
        if titulo:
            o.append("<title>%s</title>" % titulo)
        if con_color and self.aguadas:
            o.append('<g class="color" stroke="none">')
            for color, op, d in self.aguadas:
                opv = op if op_color is None else op * op_color
                o.append('<path fill="%s" fill-opacity="%s" d="%s"/>' % (color, fnum2(opv), d))
            o.append("</g>")
        o.append('<g class="linea" fill="none" stroke="%s" stroke-linecap="round" '
                 'stroke-linejoin="round">' % TINTA)
        orden = {"c": 0, "d": 1, "s": 2}
        grupos = {}
        for fam, w, n, d in self.trazos:
            grupos.setdefault((orden[fam], w), []).append((n, d))
        for (of, w), lst in sorted(grupos.items()):
            o.append('<g stroke-width="%s">' % fnum2(w))
            for n, d in sorted(lst):
                o.append('<path class="l" pathLength="1" d="%s"/>' % d)
            o.append("</g>")
        o.extend(self.extra_linea)
        o.append("</g>")
        o.append("</svg>")
        return "\n".join(o) + "\n"


def fnum2(v):
    """Como fnum pero con 2 decimales (opacidades, grosores)."""
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    return s or "0"


# ----------------------------------------------------------------------------
# utilidades internas
# ----------------------------------------------------------------------------

def _rotar(p, c, a):
    ca, sa = math.cos(a), math.sin(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def _extender(pts, esquinas, e0, e1):
    """Alarga (e>0) o recorta (e<0) la polilínea por sus extremos."""
    pts = list(pts)
    esquinas = set(esquinas)
    L = longitud(pts)
    if e0 + e1 < -L * 0.6:
        f = (L * 0.6) / max(1e-6, -(e0 + e1))
        e0 *= f
        e1 *= f
    if e0 < 0:
        pts, esquinas = _recortar_ini(pts, esquinas, -e0)
    elif e0 > 0 and len(pts) > 1:
        t = unit((pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]))
        pts.insert(0, (pts[0][0] + t[0] * e0, pts[0][1] + t[1] * e0))
        esquinas = {k + 1 for k in esquinas}
    if e1 < 0:
        r = list(reversed(pts))
        n = len(pts)
        er = {n - 1 - k for k in esquinas}
        r, er = _recortar_ini(r, er, -e1)
        n2 = len(r)
        pts = list(reversed(r))
        esquinas = {n2 - 1 - k for k in er}
    elif e1 > 0 and len(pts) > 1:
        t = unit((pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]))
        pts.append((pts[-1][0] + t[0] * e1, pts[-1][1] + t[1] * e1))
    return pts, esquinas


def _recortar_ini(pts, esquinas, e):
    acc = 0.0
    for i in range(len(pts) - 1):
        L = dist(pts[i], pts[i + 1])
        if acc + L >= e:
            p = lerp(pts[i], pts[i + 1], (e - acc) / max(L, 1e-9))
            nuevo = [p] + pts[i + 1:]
            esq = {k - i for k in esquinas if k > i}
            return nuevo, esq
        acc += L
    return pts[-2:], set()


def _cortar(pts, esquinas, s0, s1):
    """Parte la polilínea quitando el tramo [s0, s1] de longitud de arco."""
    a, ea, b, eb = [pts[0]], set(), [], set()
    acc = 0.0
    fase = 0
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        L = dist(p, q)
        if fase == 0:
            if acc + L >= s0:
                a.append(lerp(p, q, (s0 - acc) / max(L, 1e-9)))
                fase = 1
            else:
                a.append(q)
                if i + 1 in esquinas:
                    ea.add(len(a) - 1)
        if fase == 1:
            if acc + L >= s1:
                b.append(lerp(p, q, (s1 - acc) / max(L, 1e-9)))
                b.append(q)
                if i + 1 in esquinas:
                    eb.add(len(b) - 1)
                fase = 2
        elif fase == 2:
            b.append(q)
            if i + 1 in esquinas:
                eb.add(len(b) - 1)
        acc += L
    if len(b) < 2:
        return a, ea, [], set()
    return a, ea, b, eb


def trazado(P, esquinas, cerrado=False, dec=1):
    """Datos «d» compactos: Catmull-Rom (c + s) entre esquinas; rectas si solo hay 2 puntos."""
    d = Datos(dec)
    n = len(P)
    if n < 2:
        return ""
    d.M(P[0])
    if cerrado:
        # Catmull-Rom cerrada
        Q = list(P)
        m = len(Q)
        for i in range(m):
            p0, p1, p2, p3 = Q[i - 1], Q[i], Q[(i + 1) % m], Q[(i + 2) % m]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            if i == 0:
                d.c(c1, c2, p2)
            else:
                d.s(c2, p2)
        d.z()
        return d.texto()
    # tramos entre esquinas
    cortes = [0] + sorted(k for k in esquinas if 0 < k < n - 1) + [n - 1]
    for a, b in zip(cortes[:-1], cortes[1:]):
        tramo = P[a:b + 1]
        m = len(tramo)
        if m == 2:
            d.l(tramo[1])
            continue
        ext = [(2 * tramo[0][0] - tramo[1][0], 2 * tramo[0][1] - tramo[1][1])] + tramo + \
              [(2 * tramo[-1][0] - tramo[-2][0], 2 * tramo[-1][1] - tramo[-2][1])]
        for i in range(m - 1):
            p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            if i == 0:
                d.c(c1, c2, p2)
            else:
                d.s(c2, p2)
    return d.texto()


def _poli_datos(P, dec=0):
    d = Datos(dec)
    d.M(P[0])
    for p in P[1:]:
        d.l(p)
    d.z()
    return d.texto()
