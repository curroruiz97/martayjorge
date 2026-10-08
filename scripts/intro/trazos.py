"""Etapa 2: esqueleto raster -> grafo -> trazos de pluma ordenados (polilíneas en unidades de fuente).

Entrada: glifos.pkl (de glifos.py). Salida: trazos.pkl + debug_trazos.png.
"""
import math
import pickle
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.morphology import remove_small_holes, skeletonize

ESC = 0.6
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Preferencias de inicio por glifo: (u, v) en [0,1] dentro de la caja del glifo (0,0 = arriba-izquierda).
# Se afinan a ojo viendo debug_trazos.png.
INICIO = {
    "M": (0.0, 1.0),
    "a": (0.9, 0.1),
    "r": (0.1, 0.0),
    "t.ss01": (0.5, 0.0),
    "a.ss01": (0.9, 0.1),
    "y": (0.0, 0.1),
    "J": (0.0, 0.0),
    "o": (0.6, 0.0),
    "g.ss01": (0.9, 0.1),
    "e.ss01": (0.0, 0.5),
}


def vecinos_limpios(pix):
    """Adyacencia 8-conexa sin diagonales redundantes (así línea=2, extremo=1, cruce>=3)."""
    nb = {}
    for p in pix:
        l = []
        for dy, dx in N8:
            q = (p[0] + dy, p[1] + dx)
            if q in pix:
                if dy != 0 and dx != 0 and ((p[0] + dy, p[1]) in pix or (p[0], p[1] + dx) in pix):
                    continue  # diagonal redundante
                l.append(q)
        nb[p] = l
    return nb


def construir_grafo(sk):
    ys, xs = np.nonzero(sk)
    pix = set(zip(ys.tolist(), xs.tolist()))
    nb = vecinos_limpios(pix)
    grado = {p: len(v) for p, v in nb.items()}
    esp = [p for p in pix if grado[p] != 2]
    # agrupar cruces adyacentes
    grupo = {}
    nodos = []
    for p in esp:
        if p in grupo:
            continue
        cola, comp = [p], [p]
        grupo[p] = len(nodos)
        while cola:
            c = cola.pop()
            for q in nb[c]:
                if q in grupo or grado[q] == 2:
                    continue
                if grado[q] >= 3 and grado[c] >= 3:
                    grupo[q] = len(nodos); cola.append(q); comp.append(q)
        cy = sum(c[0] for c in comp) / len(comp); cx = sum(c[1] for c in comp) / len(comp)
        nodos.append({"pix": set(comp), "c": (cy, cx), "ext": all(grado[c] == 1 for c in comp)})
    # trazar aristas entre nodos
    aristas, vistos = [], set()
    for ni, nd in enumerate(nodos):
        for s in nd["pix"]:
            for q in nb[s]:
                if q in nd["pix"] or q in grupo:
                    continue
                if (s, q) in vistos:
                    continue
                camino = [nd["c"], (float(q[0]), float(q[1]))]
                prev, cur = s, q
                vistos.add((s, q))
                fin = None
                while True:
                    if cur in grupo:
                        fin = grupo[cur]; break
                    sig = [r for r in nb[cur] if r != prev]
                    if not sig:
                        break
                    nxt = sig[0]
                    camino.append((float(nxt[0]), float(nxt[1])))
                    prev, cur = cur, nxt
                if fin is None:
                    continue
                camino[-1] = nodos[fin]["c"]
                vistos.add((cur, prev))
                aristas.append({"a": ni, "b": fin, "pts": camino})
    # anillos sin nodos (ciclos puros)
    en_aristas = set()
    for a in aristas:
        for pt in a["pts"]:
            en_aristas.add((int(round(pt[0])), int(round(pt[1]))))
    resto = pix - en_aristas - set().union(*[n["pix"] for n in nodos]) if nodos else set(pix)
    return nodos, aristas, nb, resto


def longitud(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def podar(nodos, aristas, umbral):
    """Elimina espuelas cortas (extremo libre -> cruce) y contrae nodos de grado 2."""
    cambio = True
    while cambio:
        cambio = False
        grado = defaultdict(int)
        for e in aristas:
            grado[e["a"]] += 1; grado[e["b"]] += 1
        for e in list(aristas):
            if len(aristas) <= 1:
                break
            ext_a, ext_b = grado[e["a"]] == 1, grado[e["b"]] == 1
            if (ext_a != ext_b) and longitud(e["pts"]) < umbral:
                cruce = e["b"] if ext_a else e["a"]
                if grado[cruce] >= 3:
                    aristas.remove(e); cambio = True; break
        # contraer nodos de grado 2 (une dos aristas en una)
        grado = defaultdict(list)
        for i, e in enumerate(aristas):
            grado[e["a"]].append(i); grado[e["b"]].append(i)
        for n, idxs in grado.items():
            if len(idxs) == 2 and idxs[0] != idxs[1]:
                e1, e2 = aristas[idxs[0]], aristas[idxs[1]]
                p1 = e1["pts"] if e1["b"] == n else e1["pts"][::-1]
                o1 = e1["a"] if e1["b"] == n else e1["b"]
                p2 = e2["pts"] if e2["a"] == n else e2["pts"][::-1]
                o2 = e2["b"] if e2["a"] == n else e2["a"]
                nuevo = {"a": o1, "b": o2, "pts": p1 + p2[1:]}
                aristas.remove(e1); aristas.remove(e2); aristas.append(nuevo)
                cambio = True
                break
    return aristas


def angulo_salida(pts, desde_inicio, n=14):
    """Dirección (rad) de la arista en su extremo, mirando hacia dentro de la arista (desde_inicio) o hacia fuera."""
    if desde_inicio:
        a, b = pts[0], pts[min(n, len(pts) - 1)]
    else:
        a, b = pts[-1], pts[max(-n - 1, -len(pts))]
    return math.atan2(b[0] - a[0], b[1] - a[1])


def diferencia(a, b):
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def extraer_trazos(nodos, aristas, pref, caja):
    """Cubre todas las aristas con trazos continuos. pref=(u,v) -> punto de inicio preferido."""
    y0, y1, x0, x1 = caja
    objetivo = (y0 + pref[1] * (y1 - y0), x0 + pref[0] * (x1 - x0))
    sin_visitar = set(range(len(aristas)))
    adj = defaultdict(list)
    for i, e in enumerate(aristas):
        adj[e["a"]].append(i); adj[e["b"]].append(i)
    trazos = []
    ultimo = objetivo
    while sin_visitar:
        # nodos candidatos con aristas sin visitar: preferir extremos (grado 1)
        cand = []
        for n in adj:
            inc = [i for i in adj[n] if i in sin_visitar]
            if inc:
                esx = len(adj[n]) == 1
                cand.append((0 if esx else 1, math.dist(nodos[n]["c"], ultimo), n))
        cand.sort()
        # entre extremos, el más cercano al objetivo (o al final del trazo anterior)
        n = cand[0][2]
        cur = n
        poly = []
        entrada = None
        while True:
            opciones = [i for i in adj[cur] if i in sin_visitar]
            if not opciones:
                break
            if entrada is None:
                i = max(opciones, key=lambda k: longitud(aristas[k]["pts"]))
            else:
                def giro(k):
                    e = aristas[k]
                    sal = angulo_salida(e["pts"], e["a"] == cur)
                    return diferencia(sal, (entrada + math.pi) % (2 * math.pi))
                # menor giro = más recto (la dirección de entrada invertida es la "salida" opuesta)
                i = min(opciones, key=giro)
            e = aristas[i]
            pts = e["pts"] if e["a"] == cur else e["pts"][::-1]
            otro = e["b"] if e["a"] == cur else e["a"]
            poly += pts if not poly else pts[1:]
            sin_visitar.discard(i)
            entrada = angulo_salida(pts[::-1], True)  # dirección con la que llegamos (apunta hacia atrás)
            entrada = (entrada + math.pi) % (2 * math.pi) if False else entrada
            cur = otro
        trazos.append(poly)
        ultimo = poly[-1]
    return trazos


def suavizar(pts, k=5):
    p = np.array(pts, dtype=float)
    if len(p) < 3:
        return p
    out = p.copy()
    for i in range(1, len(p) - 1):
        a, b = max(0, i - k), min(len(p), i + k + 1)
        out[i] = p[a:b].mean(axis=0)
    return out


def rdp(p, eps):
    if len(p) < 3:
        return p
    a, b = p[0], p[-1]
    ab = b - a
    n = np.linalg.norm(ab)
    if n == 0:
        d = np.linalg.norm(p - a, axis=1)
    else:
        d = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / n
    i = int(np.argmax(d))
    if d[i] > eps:
        l = rdp(p[: i + 1], eps); r = rdp(p[i:], eps)
        return np.vstack([l[:-1], r])
    return np.vstack([a, b])


def main():
    G = pickle.load(open("glifos.pkl", "rb"))
    res = {}
    imgs = []
    for palabra, v in G.items():
        res[palabra] = []
        for g in v["glifos"]:
            mask = remove_small_holes(g["mask"], max_size=500)
            sk = skeletonize(np.ascontiguousarray(mask))
            dist = ndi.distance_transform_edt(mask)
            r_max = float(dist[sk].max()) if sk.any() else 10
            r_med = float(np.median(dist[sk]))
            nodos, aristas, nb, resto = construir_grafo(sk)
            umbral = 1.15 * r_max * 1.6   # espuelas más cortas que ~1.8 radios se eliminan
            aristas = podar(nodos, aristas, umbral)
            ys, xs = np.nonzero(g["mask"])
            caja = (ys.min(), ys.max(), xs.min(), xs.max())
            trazos = extraer_trazos(nodos, aristas, INICIO.get(g["name"], (0, 0)), caja)
            # suavizar + simplificar (en px de raster)
            tr = []
            for t in trazos:
                s = suavizar(t, 4)
                s = rdp(s, 1.4)
                tr.append(s)
            res[palabra].append({"name": g["name"], "x": g["x"], "trazos_px": tr, "r_max": r_max, "r_med": r_med, "org": g["org"], "d": g["d"], "mask": g["mask"], "shape": g["mask"].shape})
            print(palabra, g["name"], "trazos:", len(tr), "· longitud px:", [int(longitud(list(map(tuple, t)))) for t in tr], "· r_max %.1f" % r_max)
            # imagen de depuración
            rgb = np.zeros(g["mask"].shape + (3,), dtype=np.uint8) + 255
            rgb[g["mask"]] = (225, 225, 225)
            im = Image.fromarray(rgb)
            dr = ImageDraw.Draw(im)
            cols = [(214, 40, 40), (30, 120, 220), (20, 150, 60), (200, 120, 0), (140, 40, 200), (0, 150, 150)]
            for k, t in enumerate(tr):
                c = cols[k % len(cols)]
                dr.line([(float(a[1]), float(a[0])) for a in t], fill=c, width=3)
                a0 = t[0]
                dr.ellipse([a0[1] - 7, a0[0] - 7, a0[1] + 7, a0[0] + 7], outline=c, width=3)
                dr.text((a0[1] + 9, a0[0] - 9), str(k + 1), fill=c)
            imgs.append(im)
    pickle.dump(res, open("trazos.pkl", "wb"))
    H = max(i.height for i in imgs); W = sum(i.width for i in imgs) + 10 * len(imgs)
    sheet = Image.new("RGB", (W, H), (255, 255, 255)); x = 0
    for i in imgs:
        sheet.paste(i, (x, 0)); x += i.width + 10
    sheet.save("debug_trazos.png")
    print("hoja", sheet.size)


if __name__ == "__main__":
    main()
