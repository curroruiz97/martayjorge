"""Etapa 3: ajustes de orden/sentido, grosor mínimo de cobertura, layout y SVG con la cronología de escritura.

Entrada: trazos.pkl. Salida: nombres.svg (fragmento para incrustar) + informe de cobertura.
"""
import math
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw

ESC = 0.6
PAD = 40

# ---- Ajustes manuales (índices de trazo 1-based dentro de cada glifo, tal como salen numerados en debug_trazos.png) ----
#   ("inv", k)           invierte el sentido del trazo k (para que se escriba como lo haría una mano)
#   ("fus", i, j, inv)   pega al final del trazo i el trazo j (invertido si inv) y elimina el j
#   ("partir", k, ref)   parte el trazo k por el punto más cercano al último punto del trazo ref: queda en dos (k y k+1)
# Los índices valen en el estado actual: tras un «partir», los trazos siguientes se desplazan una posición.
AJUSTES = {
    "M": [("inv", 2), ("inv", 3)],                     # las dos subidas finas se escriben de abajo arriba y luego bajan
    "a": [("inv", 2)],                                 # el cierre baja por el palo y sale hacia la derecha
    "r": [("inv", 2)],                                 # el hombro parte del palo
    "t": [("fus", 3, 2, True)],                        # el travesaño de izquierda a derecha, de una vez
    "y": [("inv", 3)],
    "J": [("partir", 1, 2), ("fus", 1, 3, True)],      # primero la barra de arriba entera, luego el palo con su gancho
    "o": [("inv", 1), ("inv", 2)],                     # el óvalo en sentido antihorario y el empalme hacia la derecha
    "g": [("inv", 2)],
    "e": [("inv", 1)],                                 # empieza dentro del ojo y sale por la derecha
}
# (la velocidad de escritura, las pausas y la composición de las tres palabras están en svg.py)
GRUESO_K = 1.0           # factor sobre el grosor de cobertura calculado


def px2u(p, org):
    """(fila, col) del raster -> (x, y) en unidades de fuente (y hacia arriba)."""
    x0, y1 = org
    return ((p[1] - PAD) / ESC + x0, y1 - (p[0] - PAD) / ESC)


def largo(poly):
    return sum(math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1))


def cobertura(mask, trazos_px, w_px):
    """Fracción del glifo cubierta por los trazos gruesos (redondeados)."""
    im = Image.new("L", (mask.shape[1], mask.shape[0]), 0)
    d = ImageDraw.Draw(im)
    r = w_px / 2
    for t in trazos_px:
        pts = [(float(p[1]), float(p[0])) for p in t]
        d.line(pts, fill=255, width=int(round(w_px)), joint="curve")
        for (x, y) in pts:
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    cub = np.array(im) > 0
    total = mask.sum()
    return float((cub & mask).sum() / total)



def _salida_rayo(mask, p, d, max_px=140):
    """Distancia (px) que se puede avanzar desde p en la dirección d sin salir de la máscara."""
    H, W = mask.shape
    n = 0
    while n < max_px:
        r = int(round(p[0] + d[0] * (n + 1))); c = int(round(p[1] + d[1] * (n + 1)))
        if r < 0 or c < 0 or r >= H or c >= W or not mask[r, c]:
            break
        n += 1
    return n


def completar(tr, mask, w_px, ang_min=50.0):
    """Añade «pinchazos» hacia el borde en vértices agudos y en los extremos de cada trazo."""
    out = []
    for P in tr:
        P = np.array(P, dtype=float)
        pts = []
        n = len(P)
        for i in range(n):
            v = P[i]
            pts.append(v)
            d = None
            if i == 0 and n > 1:
                d = P[0] - P[1]
            elif i == n - 1 and n > 1:
                d = P[-1] - P[-2]
            elif 0 < i < n - 1:
                a = P[i] - P[i - 1]; b = P[i + 1] - P[i]
                la, lb = np.linalg.norm(a), np.linalg.norm(b)
                if la > 1e-6 and lb > 1e-6:
                    cosv = float(np.clip(np.dot(a, b) / (la * lb), -1, 1))
                    giro = math.degrees(math.acos(cosv))
                    if giro > ang_min:
                        d = a / la - b / lb
            if d is None:
                continue
            nd = np.linalg.norm(d)
            if nd < 1e-6:
                continue
            d = d / nd
            dist = _salida_rayo(mask, v, d)
            ext = dist - 0.5 * w_px * 0.9
            if ext > 2:
                q = v + d * ext
                if i == 0:
                    pts.pop(); pts.append(q); pts.append(v)      # el trazo empieza en el borde
                elif i == n - 1:
                    pts.append(q)                                # y termina en el borde
                else:
                    pts.append(q); pts.append(v)                 # pico y vuelta
        out.append(np.array(pts))
    return out



def _cubierta(shape, tr, w_px):
    im = Image.new("L", (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    r = w_px / 2
    for t in tr:
        pts = [(float(p[1]), float(p[0])) for p in t]
        d.line(pts, fill=255, width=int(round(w_px)), joint="curve")
        for (x, y) in pts:
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return np.array(im) > 0


def completar_huecos(tr, mask, w_px, umbral=50, max_iter=60):
    """Cubre las zonas de la letra que el trazo base no alcanza (picos, extremos, nudos):
    para cada hueco inserta un pinchazo desde el vértice más cercano (ocurre en el momento correcto)."""
    from scipy import ndimage as ndi
    tr = [np.array(t, dtype=float) for t in tr]
    previo = None
    for _ in range(max_iter):
        cub = _cubierta(mask.shape, tr, w_px)
        unc = mask & ~cub
        lab, n = ndi.label(unc)
        if n == 0:
            break
        areas = ndi.sum(unc, lab, index=range(1, n + 1))
        k = int(np.argmax(areas)) + 1
        if areas[k - 1] < umbral or (previo is not None and areas[k - 1] >= previo):
            break
        previo = areas[k - 1]
        ys, xs = np.nonzero(lab == k)
        dist_cub = ndi.distance_transform_edt(~cub)
        i = int(np.argmax(dist_cub[ys, xs]))
        q = np.array([ys[i], xs[i]], dtype=float)
        mejor = None
        for si, t in enumerate(tr):
            d = np.linalg.norm(t - q, axis=1)
            j = int(np.argmin(d))
            if mejor is None or d[j] < mejor[0]:
                mejor = (d[j], si, j)
        _, si, j = mejor
        t = tr[si]; v = t[j]
        dv = q - v; L = float(np.linalg.norm(dv))
        q2 = v + dv * (max(0.0, L - 0.45 * w_px) / L) if L > 0 else q
        if j == len(t) - 1:
            tr[si] = np.vstack([t, q2])
        elif j == 0:
            tr[si] = np.vstack([q2, t])
        else:
            tr[si] = np.vstack([t[: j + 1], q2, t[j:]])
        previo = None
    return tr


def aplicar_ajustes(nombre, tr):
    tr = [np.array(t, dtype=float) for t in tr]
    for op in AJUSTES.get(nombre, []):
        if op[0] == "inv":
            tr[op[1] - 1] = tr[op[1] - 1][::-1]
        elif op[0] == "fus":
            _, i, j, inv = op
            a, b = tr[i - 1], tr[j - 1]
            if inv:
                b = b[::-1]
            tr[i - 1] = np.vstack([a, b[1:]])
            tr[j - 1] = None
        elif op[0] == "partir":
            _, k, ref = op
            t, p = tr[k - 1], tr[ref - 1][-1]
            idx = int(np.argmin(np.linalg.norm(t - p, axis=1)))
            tr[k - 1:k] = [t[: idx + 1], t[idx:]]
    return [t for t in tr if t is not None]


def procesar_glifo(g):
    tr = aplicar_ajustes(g["name"], g["trazos_px"])
    # ancho base proporcional al trazo típico; se completan ápices/extremos; si falta cobertura se engorda
    w = 2 * g["r_med"] * 1.25
    tr2 = completar_huecos(tr, g["mask"], w)
    while cobertura(g["mask"], tr2, w) < 0.992 and w < 2 * g["r_max"] * 1.7:
        w += 2
        tr2 = completar_huecos(tr, g["mask"], w)
    tr = tr2
    cob = cobertura(g["mask"], tr, w)
    w = w * GRUESO_K
    return tr, w / ESC, cob  # grosor en unidades de fuente


def path_d(poly_u):
    pts = poly_u
    s = "M%d %d" % (round(pts[0][0]), round(pts[0][1]))
    for p in pts[1:]:
        s += "L%d %d" % (round(p[0]), round(p[1]))
    return s


def main():
    R = pickle.load(open("trazos.pkl", "rb"))
    palabras = {}
    for palabra, glifos in R.items():
        out = []
        for g in glifos:
            tr, w_u, cob = procesar_glifo(g)
            trazos_u = [[px2u(p, g["org"]) for p in t] for t in tr]
            out.append({"name": g["name"], "x": g["x"], "trazos": trazos_u, "w": w_u, "d": g["d"], "cob": cob})
            print("%-6s %-7s trazos=%d  grosor=%.0f u  cobertura=%.2f%%" % (palabra, g["name"], len(tr), w_u, cob * 100))
        palabras[palabra] = out
    pickle.dump(palabras, open("palabras.pkl", "wb"))


if __name__ == "__main__":
    main()
