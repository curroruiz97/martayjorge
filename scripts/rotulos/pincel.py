"""Motor de PINCEL SECO (numpy + Pillow, sin más dependencias).

Cómo pinta un trazo:
  1. El esqueleto (curva Catmull-Rom o recta) se muestrea cada píxel de supermuestreo.
  2. Presión a lo largo del trazo: ataque, un poco de pigmento encharcado al empezar, cuerpo con
     ruido suave y salida afilada. El ancho sigue a la presión.
  3. El pincel son N cerdas repartidas a lo ancho. Cada una tiene su carga, se va secando
     (la tinta del pincel se agota con la distancia recorrida), los flancos van más secos y
     al final del trazo las cerdas se abren (se deshilacha).
  4. Lo que deposita cada cerda se acumula (salpicado bilineal) y se funde con un desenfoque
     de caja muy corto.
  5. Grano de papel: el pigmento agarra primero en los «picos» del papel. Donde el pincel va
     cargado se cubre todo; donde va seco solo los picos → estrías que siguen la dirección del
     trazo y bordes rasgados.
  6. Superposiciones un poco más oscuras y un granulado leve del color.
Todo se pinta a 4× y se reduce al final (media de bloques con alfa premultiplicado).
Semillas fijas (np.random.RandomState): mismas semillas → mismas imágenes.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'ilustraciones'))
from pluma import catmull_denso  # noqa: E402

import alfabeto  # noqa: E402

# Tintas de acuarela, claras y suaves (lo pidieron así tras ver las muestras con rojo ladrillo y negro)
TERRACOTA = (186, 98, 76)        # #ba624c · títulos y nombres
GRIS_PAYNE = (104, 112, 122)     # #68707a · acentos (la «y» de los nombres, «S.R.C.»): el negro, aguado
ROJO_LADRILLO = (168, 74, 51)    # #a84a33 (= --rojo de la web): botones, más denso para que el texto blanco se lea
NEGRO = (35, 31, 28)             # negro cálido de tinta china (solo para pruebas)
BLANCO = (255, 255, 255)         # para máscaras

# Estilos de pincel (todas las medidas relativas a la altura de la mayúscula o del trazo)
ESTILOS = {
    # rotulado de títulos y nombres
    # (densidad baja: la tinta es transparente, como una acuarela, y los cruces se notan)
    'rotulo': dict(ancho=0.19, cerdas=72, carga=1.55, recorrido=1.5, fin=(0.42, 0.62), seco=0.55,
                   umbral=(0.16, 0.62), suavidad=0.07, densidad=1.7, temblor=0.012),
    # más seco: más estrías y bordes más rotos
    'rotulo-seco': dict(ancho=0.19, cerdas=72, carga=1.35, recorrido=1.15, fin=(0.32, 0.5), seco=0.7,
                        umbral=(0.18, 0.66), suavidad=0.06, densidad=2.5, temblor=0.014),
    # más cargado: casi lleno, la textura solo en los finales
    'rotulo-cargado': dict(ancho=0.2, cerdas=72, carga=1.85, recorrido=2.0, fin=(0.55, 0.75), seco=0.45,
                           umbral=(0.15, 0.6), suavidad=0.08, densidad=2.8, temblor=0.01),
}


def suave(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ruido1d(s, rng, largo):
    """Ruido de valor 1D en [-1, 1] a lo largo de s, con nudos cada `largo`."""
    k = s / max(largo, 1e-6)
    n = int(k[-1]) + 3
    v = rng.uniform(-1.0, 1.0, n)
    i = np.floor(k).astype(np.int64)
    t = k - i
    t = t * t * (3.0 - 2.0 * t)
    return v[i] * (1.0 - t) + v[i + 1] * t


def ruido_valor(h, w, celda, rng):
    """Ruido de valor 2D suave en [0, 1] (rejilla aleatoria ampliada con bicúbica)."""
    gh, gw = int(h / celda) + 3, int(w / celda) + 3
    g = rng.random_sample((gh, gw)).astype(np.float32)
    im = Image.fromarray(g, mode='F').resize((int(math.ceil(gw * celda)), int(math.ceil(gh * celda))), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32)[:h, :w]


def papel(h, w, ss, semilla):
    """Relieve del papel de acuarela en [0, 1] (1 = pico). Tres escalas de grano (en px finales; el más fino no
    baja de 1,3 px: por debajo del píxel solo añade ruido que encarece las imágenes sin verse)."""
    rng = np.random.RandomState(semilla)
    g = np.zeros((h, w), np.float32)
    for celda, peso in ((1.3, 0.45), (3.0, 0.4), (9.0, 0.15)):
        g += peso * ruido_valor(h, w, celda * ss, rng)
    lo, hi = np.percentile(g, [2, 98])
    return np.clip((g - lo) / (hi - lo), 0.0, 1.0)


def caja(a, r):
    """Desenfoque de caja separable de radio r (sumas acumuladas)."""
    if r <= 0:
        return a
    k = 2 * r + 1
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r)), mode='edge'), axis=1, dtype=np.float64)
    a = ((c[:, k:] - c[:, :-k]) / k).astype(np.float32)
    c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0)), mode='edge'), axis=0, dtype=np.float64)
    return ((c[k:, :] - c[:-k, :]) / k).astype(np.float32)


def salpicar(F, X, Y, V):
    """Suma V en F en las posiciones (X, Y) con reparto bilineal."""
    h, w = F.shape
    x0 = np.floor(X).astype(np.int64)
    y0 = np.floor(Y).astype(np.int64)
    fx = (X - x0).astype(np.float32)
    fy = (Y - y0).astype(np.float32)
    for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xi, yi = x0 + dx, y0 + dy
        ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        F += np.bincount(yi[ok] * w + xi[ok], weights=(V * wt)[ok], minlength=h * w).reshape(h, w).astype(np.float32)


def remuestrear(P, paso=1.0):
    """Puntos equiespaciados (paso en px) a lo largo de la polilínea P (array n×2)."""
    d = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(d)])
    L = float(s[-1])
    n = max(2, int(L / paso) + 1)
    si = np.linspace(0.0, L, n)
    return np.stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])], 1), si, L


class Lienzo:
    """Lienzo transparente de ancho × alto px finales, pintado a ss× por dentro."""

    def __init__(self, ancho, alto, ss=4, semilla_papel=8052027, densidad=2.6):
        self.ancho, self.alto, self.ss = int(ancho), int(alto), ss
        self.W, self.H = self.ancho * ss, self.alto * ss
        self.G = papel(self.H, self.W, ss, semilla_papel)
        self.capas = {}          # color → densidad óptica acumulada
        self.densidad = densidad
        self.trazos = []         # (color, centro en px finales [n×2], ancho máximo en px finales)

    def _capa(self, color):
        if color not in self.capas:
            self.capas[color] = np.zeros((self.H, self.W), np.float32)
        return self.capas[color]

    def trazo(self, pts, color, est, rng, ancho, tipo='c', recorte=0.0, punto=False, presion=None):
        """Pinta un trazo. pts en px finales; ancho = ancho base del pincel en px finales."""
        ss = self.ss
        W0 = ancho * ss
        P = np.array([(x * ss, y * ss) for x, y in pts], dtype=np.float64)
        if punto:
            # golpe de pincel: una vuelta corta en espiral alrededor del punto → mancha redonda e irregular
            cx, cy = P.mean(axis=0)
            a0 = rng.uniform(0, math.tau)
            ang = a0 + np.linspace(0, 1.15 * math.tau, 40)
            rr = W0 * np.linspace(0.12, 0.24, 40)
            P = np.stack([cx + rr * np.cos(ang), cy + rr * np.sin(ang)], 1)
            W0 *= 0.62
            tipo = 'c'
        if tipo == 'c' and len(P) > 2:
            P = np.array(catmull_denso([tuple(p) for p in P], paso=1.0))
        P, s, L = remuestrear(P, 1.0)
        if recorte > 0:                                   # «no cierra del todo»
            m = max(2, int(len(s) * (1 - recorte)))
            P, s, L = P[:m], s[:m], float(s[m - 1])
        if L < 2:
            return
        n = len(s)
        u = s / L
        # tangentes suavizadas y normales
        T = np.gradient(P, axis=0)
        v = max(3, int(W0 / 4)) | 1
        ker = np.ones(v) / v
        T = np.stack([np.convolve(np.pad(T[:, i], v // 2, mode='edge'), ker, mode='valid') for i in (0, 1)], 1)
        T /= np.maximum(np.hypot(T[:, 0], T[:, 1]), 1e-9)[:, None]
        Nn = np.stack([-T[:, 1], T[:, 0]], 1)

        # presión: ataque · charco al empezar · cuerpo con ruido · salida afilada
        if presion is None:
            a = rng.uniform(0.04, 0.1)
            r = rng.uniform(0.12, 0.3)
            presion = ((0.6 + 0.4 * suave(0.0, a, u)) * (1 + 0.15 * np.exp(-(u / 0.02) ** 2))
                       * (1 + 0.12 * ruido1d(s, rng, 2.5 * W0))
                       * (0.15 + 0.85 * (1 - suave(1 - r, 1.0, u)) ** 0.7))
        else:
            presion = presion(u)
        w = W0 * (0.35 + 0.65 * presion) * rng.uniform(0.88, 1.12)

        # tinta: se agota con la distancia (en alturas de pincel), con un mínimo
        recorrido = est['recorrido'] * (W0 / est['ancho']) * rng.uniform(0.8, 1.25)
        I0 = rng.uniform(0.95, 1.2)
        tinta = np.maximum(I0 * np.exp(-s / recorrido), est['fin'][0] * 0.6)

        # cerdas
        N = est['cerdas']
        o = np.sort(rng.uniform(-1.0, 1.0, N))
        car = 0.55 + 0.45 * rng.beta(2.0, 1.5, N)
        fl = 1 - est['seco'] * np.abs(o) ** 3
        q = rng.uniform(0, 1, N)
        sueltas = rng.random_sample(N) < 0.03
        o[sueltas] = np.sign(o[sueltas]) * rng.uniform(1.0, 1.15, sueltas.sum())
        car[sueltas] *= 0.25

        abre = 1 + 0.6 * np.clip((u - 0.85) / 0.15, 0, 1)
        X, Y, V = [], [], []
        for i in range(N):
            ni = 0.5 + 0.5 * ruido1d(s, rng, rng.uniform(0.6, 2.5) * W0)
            mi = 0.04 * W0 * ruido1d(s, rng, 3 * W0)
            oi = o[i] * (1 + (abre - 1) * q[i])
            off = oi * w / 2 + mi
            X.append(P[:, 0] + Nn[:, 0] * off)
            Y.append(P[:, 1] + Nn[:, 1] * off)
            V.append(presion * tinta * car[i] * fl[i] * (0.75 + 0.5 * ni) * (w / N))
        X = np.concatenate(X)
        Y = np.concatenate(Y)
        V = np.concatenate(V).astype(np.float32)

        rad = 1 + int(round(0.5 * W0 / N))
        mg = 3 * rad + 3
        x0 = max(0, int(X.min()) - mg)
        y0 = max(0, int(Y.min()) - mg)
        x1 = min(self.W, int(X.max()) + mg + 1)
        y1 = min(self.H, int(Y.max()) + mg + 1)
        if x1 <= x0 or y1 <= y0:
            return
        F = np.zeros((y1 - y0, x1 - x0), np.float32)
        salpicar(F, X - x0, Y - y0, V)
        F = caja(caja(F, rad), rad) * est['carga']
        G = self.G[y0:y1, x0:x1]
        lo, hi = est['umbral']
        th = lo + (hi - lo) * (1 - G)
        A = suave(th - est['suavidad'], th + est['suavidad'], F)
        self._capa(color)[y0:y1, x0:x1] += A * rng.uniform(0.85, 1.0)
        self.trazos.append((color, P / ss, float(w.max() / ss)))

    def relleno(self, mascara, color):
        """Suma una zona sólida (array de alfa 0..1 en px finales) a una capa: base de máscaras."""
        m = np.asarray(Image.fromarray((np.clip(mascara, 0, 1) * 255).astype(np.uint8)).resize((self.W, self.H), Image.BILINEAR),
                       dtype=np.float32) / 255
        self._capa(color)[:] += m * 3.0

    def imagen(self, granulado=True, oscurecer=True):
        """Imagen RGBA (Pillow) en px finales. Para máscaras: granulado=False, oscurecer=False (blanco puro)."""
        ss = self.ss
        acc = np.zeros((self.H, self.W, 3), np.float32)
        alfa = np.zeros((self.H, self.W), np.float32)
        gr = (1 - 0.06 * (self.G - 0.5)) if granulado else np.ones_like(self.G)
        for color, D in self.capas.items():
            a = 1 - np.exp(-self.densidad * D)
            osc = ((1 - 0.1 * np.clip(D - 1, 0, 1)) if oscurecer else 1.0) * gr
            rgb = np.array(color, np.float32) / 255
            for k in range(3):
                acc[:, :, k] = rgb[k] * osc * a + acc[:, :, k] * (1 - a)
            alfa = a + alfa * (1 - a)
        h, w = self.alto, self.ancho
        acc = acc.reshape(h, ss, w, ss, 3).mean(axis=(1, 3))
        alfa = alfa.reshape(h, ss, w, ss).mean(axis=(1, 3))
        rgb = np.where(alfa[..., None] > 1e-4, acc / np.maximum(alfa[..., None], 1e-4), 0)
        out = np.dstack([np.clip(rgb, 0, 1) * 255, np.clip(alfa, 0, 1) * 255]).round().astype(np.uint8)
        return Image.fromarray(out, 'RGBA')


def rotular(lineas, cap, estilo='rotulo', semilla=1, tinta=None, ss=4, interlinea=0.42, margen=0.3,
            margen_x=None, ancho_fijo=None, pintar=True):
    """Rotula `lineas` (lista de textos) con mayúsculas de pincel seco.

    cap      altura de la mayúscula en px finales
    tinta    función (linea, indice, caracter) → color; por defecto, terracota
    margen   aire arriba y abajo (en mayúsculas; deja sitio a tildes y al ¡); margen_x, a los lados
    pintar   False: solo mide (devuelve el lienzo vacío)
    Devuelve (Lienzo, info) con info = {'u': ancho/cap, 'letras': [...]} y, en el lienzo, los ejes
    de cada trazo (para animar la escritura).
    """
    est = ESTILOS[estilo]
    rng = np.random.RandomState(semilla)
    tinta = tinta or (lambda *_: TERRACOTA)
    # 1) maquetación en unidades de mayúscula (con la irregularidad de cada letra)
    disposicion = []
    anchos = []
    for li, texto in enumerate(lineas):
        pen = 0.0
        fila = []
        for ci, ch in enumerate(texto):
            av, trazos = alfabeto.letra(ch)
            sx = rng.uniform(0.9, 1.1)
            sy = rng.uniform(0.92, 1.08)
            rot = math.radians(rng.uniform(-3, 3))
            dy = rng.uniform(-0.04, 0.04)
            tr = rng.uniform(0.13, 0.19)
            fila.append((ch, av, trazos, pen, sx, sy, rot, dy, li, ci))
            pen += av * sx + tr
        anchos.append(pen - tr if fila else 0)
        disposicion.append(fila)
    mx = margen if margen_x is None else margen_x
    ancho_u = max(anchos) if ancho_fijo is None else ancho_fijo
    alto_u = 2 * margen + len(lineas) + (len(lineas) - 1) * interlinea
    info = {'u': ancho_u + 2 * mx, 'alto_u': alto_u, 'letras': []}
    W = int(math.ceil((ancho_u + 2 * mx) * cap))
    H = int(math.ceil(alto_u * cap))
    if not pintar:
        return None, info
    lz = Lienzo(W, H, ss=ss, densidad=est['densidad'])
    for li, fila in enumerate(disposicion):
        x_ini = mx + (ancho_u - anchos[li]) / 2
        y_base = margen + li * (1 + interlinea)
        for ch, av, trazos, pen, sx, sy, rot, dy, _, ci in fila:
            cxg, cyg = av / 2, 0.5
            cr, sr = math.cos(rot), math.sin(rot)
            ox = x_ini + pen + av * sx / 2
            oy = y_base + 0.5 + dy
            color = tinta(li, ci, ch)
            n0 = len(lz.trazos)
            for tipo, pts, op in trazos:
                pts = [(x + rng.normal(0, est['temblor']), y + rng.normal(0, est['temblor'])) for x, y in pts]
                if op.get('pasa') and len(pts) == 2:
                    (ax, ay), (bx, by) = pts
                    e0, e1 = rng.uniform(0.0, 0.03), rng.uniform(0.02, 0.06)
                    pts = [(ax - (bx - ax) * e0, ay - (by - ay) * e0), (bx + (bx - ax) * e1, by + (by - ay) * e1)]
                px = []
                for x, y in pts:
                    x, y = (x - cxg) * sx, (y - cyg) * sy
                    x, y = x * cr - y * sr, x * sr + y * cr
                    px.append(((ox + x) * cap, (oy + y) * cap))
                lz.trazo(px, color, est, rng, est['ancho'] * cap, tipo=tipo,
                         recorte=rng.uniform(0.03, 0.08) if op.get('cerrado') else 0.0,
                         punto=bool(op.get('punto')))
            info['letras'].append((ch, li, ci, n0, len(lz.trazos)))
    return lz, info
