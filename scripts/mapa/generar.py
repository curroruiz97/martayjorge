"""Dibuja el plano ilustrado del centro de Valladolid para la sección Alojamiento de la V3
(public/assets/mapa/valladolid-v3.svg). Sin API ni clave: es una imagen fija.

  python3 scripts/mapa/generar.py

Datos: OpenStreetMap (© colaboradores de OpenStreetMap, licencia ODbL; la atribución va en la página).
La primera vez descarga 9 teselas de la API de OSM a scripts/mapa/.cache/ (unos 23 MB, fuera de git); las
siguientes usa esa copia. Para refrescarlas, borra la carpeta.

Qué dibuja: fondo beige, parques y jardines en verde, río Pisuerga en azul, calles en blanco (más anchas cuanto
más importantes) y el óvalo de la zona recomendada entre la Plaza del Poniente y San Pablo (a pincel: relleno suave
y dos pasadas de trazo). Los iconos de los dos lugares (san-pablo.svg, autocar.svg) y los rótulos NO van dentro:
los pone el HTML encima, para que tengan el mismo tamaño en el móvil y en el ordenador. Este script imprime sus
posiciones en % para copiarlas a v3/index.html.
"""
import math
import random
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
CACHE = AQUI / ".cache"
CARPETA = RAIZ / "public" / "assets" / "mapa"
SALIDA = CARPETA / "valladolid-v3.svg"

# Lugares (docs/datos-verificados.md)
SAN_PABLO = (41.65710, -4.72442)
PONIENTE = (41.65316, -4.73128)
REFERENCIAS = {   # rótulos pequeños de orientación (los pone el HTML)
    "plaza-mayor": (41.65225, -4.72861),
    "catedral": (41.65275, -4.72343),
    "rio": (41.65640, -4.73480),
}

# Encuadre: centro entre los dos lugares, 1500 × 1125 m (4:3)
CENTRO = ((SAN_PABLO[0] + PONIENTE[0]) / 2, (SAN_PABLO[1] + PONIENTE[1]) / 2 + 0.0004)
ANCHO, ALTO = 1500.0, 1125.0
KY = 111320.0
KX = KY * math.cos(math.radians(CENTRO[0]))

# Teselas de la API de OSM (cada una ≈ 0,0065° × 0,009°; la API limita el número de nodos por petición)
TESELAS = [(lat, lng) for lat in (41.6440, 41.6505, 41.6570) for lng in (-4.7400, -4.7310, -4.7220)]

PAPEL, CALLE, BORDE = "#f1e7d4", "#fffdf8", "#e2d3ba"
VERDE, VERDE_OSC, AGUA = "#d3e3bd", "#bfd4a6", "#b7d8e2"
ROJO, TINTA = "#b23a40", "#4b3c37"

# ancho de cada tipo de calle, en metros del plano
CALLES = {
    "trunk": 20, "primary": 18, "secondary": 15, "tertiary": 12, "trunk_link": 10, "secondary_link": 10,
    "tertiary_link": 9, "residential": 8.5, "living_street": 7.5, "pedestrian": 7.5, "unclassified": 8,
    "service": 5, "footway": 3.2, "cycleway": 3, "path": 2.6, "steps": 3,
}
FINAS = {"footway", "cycleway", "path", "steps", "service"}
VERDES = {("leisure", "park"), ("leisure", "garden"), ("landuse", "grass"), ("landuse", "forest"),
          ("landuse", "village_green"), ("landuse", "recreation_ground"), ("natural", "scrub"), ("landuse", "flowerbed"),
          ("leisure", "playground"), ("leisure", "dog_park")}


def descargar():
    CACHE.mkdir(exist_ok=True)
    for i, (lat, lng) in enumerate(TESELAS, 1):
        f = CACHE / f"t{i}.osm"
        if f.exists():
            continue
        bbox = f"{lng},{lat},{round(lng + 0.009, 4)},{round(lat + 0.0065, 4)}"
        print("descargando", bbox)
        req = urllib.request.Request(f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}",
                                     headers={"User-Agent": "martayjorge-mapa/1.0"})
        f.write_bytes(urllib.request.urlopen(req, timeout=120).read())


def xy(lat, lng):
    """lat/lng → metros del plano (origen arriba a la izquierda)."""
    return ((lng - CENTRO[1]) * KX + ANCHO / 2, (CENTRO[0] - lat) * KY + ALTO / 2)


def leer():
    nodos, vias, rels = {}, {}, []
    for f in sorted(CACHE.glob("t*.osm")):
        r = ET.parse(f).getroot()
        for n in r.iter("node"):
            nodos[n.get("id")] = (float(n.get("lat")), float(n.get("lon")))
        for w in r.iter("way"):
            vias[w.get("id")] = ([nd.get("ref") for nd in w.iter("nd")], {t.get("k"): t.get("v") for t in w.iter("tag")})
        for rel in r.iter("relation"):
            t = {x.get("k"): x.get("v") for x in rel.iter("tag")}
            if t.get("type") == "multipolygon":
                rels.append(([(m.get("ref"), m.get("role")) for m in rel.iter("member") if m.get("type") == "way"], t))
    return nodos, vias, rels


def simplificar(pts, tol=1.2):
    """Ramer-Douglas-Peucker (un anillo cerrado se parte en dos mitades para no colapsar)."""
    if len(pts) < 3:
        return pts
    if pts[0] == pts[-1] and len(pts) > 4:
        m = len(pts) // 2
        return simplificar(pts[:m + 1], tol)[:-1] + simplificar(pts[m:], tol)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = math.hypot(dx, dy) or 1e-9
    i_max, d_max = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x0) - dx * (pts[i][1] - y0)) / n
        if d > d_max:
            i_max, d_max = i, d
    if d_max <= tol:
        return [pts[0], pts[-1]]
    return simplificar(pts[:i_max + 1], tol)[:-1] + simplificar(pts[i_max:], tol)


def dentro(pts, margen=120):
    return any(-margen <= x <= ANCHO + margen and -margen <= y <= ALTO + margen for x, y in pts)


def d_de(pts, cerrar=False):
    s = "M" + " ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return s + ("Z" if cerrar else "")


def anillos(miembros, vias):
    """Une las vías 'outer' de un multipolígono en anillos cerrados."""
    trozos = [list(vias[ref][0]) for ref, rol in miembros if rol in ("outer", "") and ref in vias]
    out = []
    while trozos:
        a = trozos.pop()
        cambiado = True
        while a[0] != a[-1] and cambiado:
            cambiado = False
            for i, b in enumerate(trozos):
                if b[0] == a[-1]:
                    a += b[1:]
                elif b[-1] == a[-1]:
                    a += b[::-1][1:]
                elif b[-1] == a[0]:
                    a = b + a[1:]
                elif b[0] == a[0]:
                    a = b[::-1] + a[1:]
                else:
                    continue
                trozos.pop(i)
                cambiado = True
                break
        out.append(a)
    return out


def ovalo(c, rx, ry, giro, semilla, deriva=0.0, vuelta=1.0, n=140):
    """Óvalo «a pincel»: contorno con armónicos suaves (siempre igual: semilla fija)."""
    rnd = random.Random(semilla)
    h = [(k, a * (0.75 + 0.5 * rnd.random()), rnd.random() * 2 * math.pi) for k, a in ((2, .012), (3, .01), (5, .006), (9, .002))]
    ini = rnd.random() * 2 * math.pi
    g = math.radians(giro)
    pts = []
    for i in range(int(n * vuelta) + 1):
        t = ini + i / n * 2 * math.pi
        s = 1 + sum(a * math.sin(k * t + f) for k, a, f in h) + deriva * max(0, i / n - .75)
        u, v = rx * s * math.cos(t), ry * s * math.sin(t)
        pts.append((c[0] + u * math.cos(g) - v * math.sin(g), c[1] - (u * math.sin(g) + v * math.cos(g))))
    return pts


def curva(pts, cerrar=False):
    """Catmull-Rom → Bézier: trazo suave para el óvalo."""
    P = pts + pts[:3] if cerrar else [pts[0]] + pts + [pts[-1]]
    s = f"M{P[1][0]:.1f} {P[1][1]:.1f}"
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        s += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return s + ("Z" if cerrar else "")


def iglesia(x, y, s=1.0):
    """San Pablo en colores planos (el mismo dibujo que el marcador de Google Maps de la V1/V2), apoyado en (x, y)."""
    piedra, sombra, detalle, hueco, puerta, tejado = "#ecd3a0", "#d9b475", "#bb8c50", "#5a463c", "#7b4a2e", "#a8643f"

    def torre(t):
        c = t + 7
        return (f'<rect x="{t}" y="21" width="14" height="51" fill="{piedra}"/>'
                f'<path d="M{t - 1} 21L{c} 7 {t + 15} 21Z" fill="{tejado}"/><path d="M{c} 7V2.5"/>'
                f'<path d="M{t + 4} 37V30a3 3 0 0 1 6 0v7Z" fill="{hueco}"/>'
                f'<rect x="{t + 5.5}" y="47" width="3" height="7" rx="1.5" fill="{hueco}"/>')
    return (f'<g transform="translate({x - 32 * s:.1f} {y - 72 * s:.1f}) scale({s})" stroke="{TINTA}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round" fill="none">'
            f'<ellipse cx="32" cy="73" rx="27" ry="2.6" fill="#2b2a28" fill-opacity=".2" stroke="none"/>'
            + torre(4) + torre(46) +
            f'<path d="M18 72V17Q32 3 46 17V72Z" fill="{piedra}"/><path d="M18 17Q32 3 46 17Z" fill="{sombra}"/>'
            f'<path d="M32 6.5V1.5M29.8 3.6h4.4"/><circle cx="32" cy="12.4" r="2.5" fill="{detalle}"/>'
            f'<rect x="21" y="20" width="22" height="20" fill="{sombra}"/>'
            f'<path d="M26.5 20v20M37.5 20v20M21 26.5h5.5M37.5 26.5H43M21 33.5h5.5M37.5 33.5H43" stroke="{detalle}" stroke-width="1.1"/>'
            f'<circle cx="32" cy="30" r="4.2" fill="#f7e9c8"/>'
            f'<path d="M21.5 72V52.5Q21.5 43.5 32 41.5 42.5 43.5 42.5 52.5V72Z" fill="{detalle}"/>'
            f'<path d="M25.8 72V55.5Q25.8 49.2 32 48 38.2 49.2 38.2 55.5V72Z" fill="{puerta}"/>'
            f'<path d="M32 49v23" stroke="#3d2a20" stroke-width="1.2"/><path d="M2 72h60"/></g>')


def autocar(x, y, s=1.0):
    """Autocar de frente-lado en colores planos, apoyado en (x, y)."""
    return (f'<g transform="translate({x - 40 * s:.1f} {y - 46 * s:.1f}) scale({s})" stroke="{TINTA}" stroke-width="1.8" '
            f'stroke-linejoin="round" stroke-linecap="round">'
            f'<ellipse cx="40" cy="45" rx="34" ry="3" fill="#2b2a28" fill-opacity=".2" stroke="none"/>'
            f'<rect x="4" y="6" width="72" height="32" rx="7" fill="{ROJO}"/>'
            f'<rect x="4" y="27" width="72" height="5" fill="#8f2b31" stroke="none"/>'
            f'<rect x="10" y="11" width="13" height="11" rx="2" fill="#e8f2f5"/><rect x="27" y="11" width="13" height="11" rx="2" fill="#e8f2f5"/>'
            f'<rect x="44" y="11" width="13" height="11" rx="2" fill="#e8f2f5"/><rect x="61" y="11" width="10" height="16" rx="2" fill="#e8f2f5"/>'
            f'<circle cx="20" cy="38" r="6" fill="#3a302c"/><circle cx="20" cy="38" r="2.2" fill="#d9d1c7" stroke="none"/>'
            f'<circle cx="60" cy="38" r="6" fill="#3a302c"/><circle cx="60" cy="38" r="2.2" fill="#d9d1c7" stroke="none"/></g>')


def main():
    descargar()
    nodos, vias, rels = leer()
    pos = lambda refs: [xy(*nodos[r]) for r in refs if r in nodos]

    verdes, aguas, rios, calles = [], [], [], {k: [] for k in CALLES}
    for refs, t in vias.values():
        pts = pos(refs)
        if len(pts) < 2 or not dentro(pts):
            continue
        cerrada = refs[0] == refs[-1]
        if cerrada and any((k, t.get(k)) in VERDES for k in ("leisure", "landuse", "natural")):
            verdes.append(d_de(simplificar(pts), True))
        elif cerrada and (t.get("natural") == "water" or t.get("leisure") == "swimming_pool"):
            aguas.append(d_de(simplificar(pts), True))
        elif t.get("waterway") in ("river", "canal"):
            rios.append(d_de(simplificar(pts, 2)))
        elif t.get("highway") in CALLES and t.get("area") != "yes" and t.get("tunnel") != "yes":
            calles[t["highway"]].append(d_de(simplificar(pts)))
    for miembros, t in rels:
        es_verde = any((k, t.get(k)) in VERDES for k in ("leisure", "landuse", "natural"))
        if es_verde or t.get("natural") == "water":
            for a in anillos(miembros, vias):
                pts = pos(a)
                if len(pts) > 2 and dentro(pts):
                    (verdes if es_verde else aguas).append(d_de(simplificar(pts), True))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO:.0f} {ALTO:.0f}" width="{ANCHO:.0f}" height="{ALTO:.0f}">',
         f'<rect width="{ANCHO:.0f}" height="{ALTO:.0f}" fill="{PAPEL}"/>',
         f'<path fill="{VERDE}" stroke="{VERDE_OSC}" stroke-width="1.2" d="{"".join(verdes)}"/>',
         f'<path fill="none" stroke="{AGUA}" stroke-width="82" stroke-linecap="round" stroke-linejoin="round" d="{"".join(rios)}"/>',
         f'<path fill="{AGUA}" d="{"".join(aguas)}"/>']
    orden = sorted(CALLES, key=lambda k: CALLES[k])
    # bordes (solo las calles de coches) y después el blanco, de las finas a las anchas
    for k in orden:
        if k not in FINAS and calles[k]:
            o.append(f'<path fill="none" stroke="{BORDE}" stroke-width="{CALLES[k] + 3}" stroke-linecap="round" stroke-linejoin="round" d="{"".join(calles[k])}"/>')
    for k in orden:
        if calles[k]:
            op = ' stroke-opacity=".8"' if k in FINAS else ""
            o.append(f'<path fill="none" stroke="{CALLE}"{op} stroke-width="{CALLES[k]}" stroke-linecap="round" stroke-linejoin="round" d="{"".join(calles[k])}"/>')

    # Óvalo de la zona recomendada: a lo largo de Poniente → San Pablo, con los dos dentro y margen
    sp, po = xy(*SAN_PABLO), xy(*PONIENTE)
    c = ((sp[0] + po[0]) / 2, (sp[1] + po[1]) / 2)
    giro = math.degrees(math.atan2(-(sp[1] - po[1]), sp[0] - po[0]))
    medio = math.hypot(sp[0] - po[0], sp[1] - po[1]) / 2
    rx, ry = medio + 200, medio * .62 + 60
    o.append(f'<path fill="{ROJO}" fill-opacity=".12" d="{curva(ovalo(c, rx, ry, giro, 20270508), True)}"/>')
    o.append(f'<path fill="none" stroke="{ROJO}" stroke-opacity=".88" stroke-width="7" stroke-linecap="round" '
             f'd="{curva(ovalo(c, rx, ry, giro, 20270508, vuelta=1.0))}"/>')
    o.append(f'<path fill="none" stroke="{ROJO}" stroke-opacity=".45" stroke-width="3" stroke-linecap="round" '
             f'd="{curva(ovalo(c, rx * 1.015, ry * 1.03, giro + 1.5, 7, vuelta=.62))}"/>')

    o.append("</svg>")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"{SALIDA.relative_to(RAIZ)}: {SALIDA.stat().st_size / 1024:.0f} KB")
    # iconos sueltos (apoyados abajo en el centro: el HTML los ancla por ahí)
    for nombre, svg, w, h in (("san-pablo", iglesia(32, 72), 64, 76), ("autocar", autocar(40, 46), 80, 50)):
        (CARPETA / f"{nombre}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{svg}</svg>\n', encoding="utf-8")
    print("Posiciones para los rótulos del HTML (left, top en %):")
    for nombre, p in [("san-pablo", SAN_PABLO), ("poniente", PONIENTE)] + list(REFERENCIAS.items()):
        x, y = xy(*p)
        print(f"  {nombre}: --x: {x / ANCHO * 100:.1f}%; --y: {y / ALTO * 100:.1f}%")


if __name__ == "__main__":
    main()
