"""Pequeña librería para dibujar ilustraciones «a acuarela» (gouache suave) con SVG.

Idea: cada objeto se compone de CAPAS de color (manchas con bordes irregulares y pigmento acumulado en el borde) y de unas
pocas LÍNEAS de tinta finas y algo temblorosas. El navegador (Chromium sin cabeza) convierte el SVG en una imagen sobre fondo
blanco; en la página se coloca con «mix-blend-mode: multiply», así el blanco desaparece y los colores se mezclan con el lino.

Todo es determinista (semillas fijas) para que, al regenerar, salgan las mismas ilustraciones.
"""
import math
import random
import re

TINTA = "#4a2c2a"      # tinta de las líneas (marrón rojizo muy oscuro)


class _Grupo:
    """with L.grupo(rot=15, cx=100, cy=200): …  → todo lo dibujado dentro se gira (y escala) alrededor de (cx, cy)."""
    def __init__(self, lienzo, rot, cx, cy, esc):
        self.L, self.rot, self.cx, self.cy, self.esc = lienzo, rot, cx, cy, esc

    def __enter__(self):
        self.ini = len(self.L.capas)
        return self

    def __exit__(self, *a):
        nuevas = self.L.capas[self.ini:]
        del self.L.capas[self.ini:]
        tr = "translate(%.1f %.1f) rotate(%.2f) scale(%.3f) translate(%.1f %.1f)" % (self.cx, self.cy, self.rot, self.esc, -self.cx, -self.cy)
        for tipo in ("mancha", "linea"):
            partes = [s for t, s in nuevas if t == tipo]
            if not partes:
                continue
            if tipo == "mancha":
                partes = ['<g style="mix-blend-mode:multiply">%s</g>' % p for p in partes]
            self.L.capas.append((tipo, '<g transform="%s">%s</g>' % (tr, "".join(partes))))


def oscurece(hex_, k):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * k), int(g * k * 0.97), int(b * k * 0.97))


def fuente_embebida():
    """@font-face con la letra de rotulado en base64, para que el texto de las ilustraciones salga con ella al renderizar."""
    import base64
    from pathlib import Path
    ruta = Path(__file__).resolve().parents[2] / "public/assets/fonts/covered-by-your-grace-latin-400-normal.woff2"
    b64 = base64.b64encode(ruta.read_bytes()).decode()
    return '@font-face{font-family:"Covered By Your Grace";src:url(data:font/woff2;base64,%s) format("woff2")}' % b64


def bbox_d(d):
    """Caja (x0, y0, x1, y1) de los puntos de control de un path con coordenadas absolutas (M, L, C, Q, Z)."""
    nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
    xs, ys = nums[0::2], nums[1::2]
    return min(xs), min(ys), max(xs), max(ys)


class Lienzo:
    def __init__(self, ancho, alto, semilla=1):
        self.w, self.h = ancho, alto
        self.rng = random.Random(semilla)
        self.capas = []     # (tipo, svg)
        self.n_filtro = 0
        self.filtros = []
        self.escala_ruido = 0.012

    # ---------- formas ----------
    def jit(self, v, a):
        return v + self.rng.uniform(-a, a)

    def suave(self, pts, cerrado=True, tension=0.5):
        """Curva suave (Catmull-Rom → Bézier cúbico) que pasa por los puntos."""
        n = len(pts)
        if n < 3:
            return "M" + " L".join("%.1f %.1f" % p for p in pts)
        d = "M%.1f %.1f" % pts[0]
        rng = range(n) if cerrado else range(n - 1)
        for i in rng:
            p0 = pts[(i - 1) % n] if (cerrado or i > 0) else pts[i]
            p1 = pts[i]
            p2 = pts[(i + 1) % n]
            p3 = pts[(i + 2) % n] if (cerrado or i + 2 < n) else p2
            k = tension / 3                      # 0,5 → Catmull-Rom clásico (la curva pasa suave por todos los puntos)
            c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
            c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
            d += "C%.1f %.1f %.1f %.1f %.1f %.1f" % (c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
        return d + ("Z" if cerrado else "")

    def blob(self, cx, cy, rx, ry, n=9, jit=0.07, rot=0.0):
        """Mancha casi elíptica con el contorno algo irregular (como pintada a mano)."""
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            k = 1 + self.rng.uniform(-jit, jit)
            x, y = math.cos(a) * rx * k, math.sin(a) * ry * k
            c, s = math.cos(rot), math.sin(rot)
            pts.append((cx + x * c - y * s, cy + x * s + y * c))
        return self.suave(pts)

    def petalo(self, cx, cy, ang, largo, ancho, punta=0.5, jit=0.05):
        """Pétalo en forma de gota: base en (cx,cy), apunta hacia «ang» (radianes)."""
        c, s = math.cos(ang), math.sin(ang)

        def P(u, v):  # u a lo largo, v de lado
            return (cx + u * c - v * s, cy + u * s + v * c)
        k = lambda: 1 + self.rng.uniform(-jit, jit)
        pts = [P(0, 0), P(largo * .22, ancho * .5 * k()), P(largo * .62, ancho * .55 * k()), P(largo * k(), 0),
               P(largo * .62, -ancho * .55 * k()), P(largo * .22, -ancho * .5 * k())]
        return self.suave(pts)

    def hoja(self, x0, y0, x1, y1, ancho, curva=0.0):
        """Hoja puntiaguda de (x0,y0) a (x1,y1)."""
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        mx, my = (x0 + x1) / 2 + nx * curva, (y0 + y1) / 2 + ny * curva
        a, b = ancho / 2, ancho / 2
        return ("M%.1f %.1f Q%.1f %.1f %.1f %.1f Q%.1f %.1f %.1f %.1f Z" %
                (x0, y0, mx + nx * a * 1.6, my + ny * a * 1.6, x1, y1, mx - nx * b * 1.6, my - ny * b * 1.6, x0, y0))

    def curva(self, pts, cerrado=False):
        return self.suave(pts, cerrado)

    # ---------- capas ----------
    def _filtro(self, tipo, d, margen):
        """Registra un filtro con su propia región (en coordenadas de usuario) y devuelve su id."""
        x0, y0, x1, y1 = bbox_d(d)
        self.n_filtro += 1
        fid = "%s%d" % (tipo, self.n_filtro)
        self.filtros.append(FILTRO[tipo].format(id=fid, x=x0 - margen, y=y0 - margen, w=(x1 - x0) + 2 * margen, h=(y1 - y0) + 2 * margen, s=self.escala_ruido))
        return fid

    def mancha(self, d, color, opacidad=0.85, rim=None, rimo=0.8):
        """Mancha de acuarela: el cuerpo (color con densidad y grano variables) y, encima, un borde de pigmento más oscuro."""
        rim = rim or oscurece(color, 0.72)
        f1, f2 = self._filtro("wcb", d, 34), self._filtro("wcr", d, 34)
        self.capas.append(("mancha", '<path d="%s" fill="%s" opacity="%.2f" filter="url(#%s)"/>'
                                     '<path d="%s" fill="%s" opacity="%.2f" filter="url(#%s)"/>' % (d, color, opacidad, f1, d, rim, rimo, f2)))

    def trazo_color(self, d, color, ancho, opacidad=0.85, rim=None, rimo=0.8):
        """Trazo grueso de color (hilos, tallos, anillos…) con el mismo aspecto de acuarela."""
        rim = rim or oscurece(color, 0.72)
        base = 'fill="none" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round"' % ancho
        m = 34 + ancho
        f1, f2 = self._filtro("wcb", d, m), self._filtro("wcr", d, m)
        self.capas.append(("mancha", '<path d="%s" %s stroke="%s" opacity="%.2f" filter="url(#%s)"/>'
                                     '<path d="%s" %s stroke="%s" opacity="%.2f" filter="url(#%s)"/>' % (d, base, color, opacidad, f1, d, base, rim, rimo, f2)))

    def linea(self, d, ancho=2.0, color=TINTA, opacidad=0.9):
        """Línea de tinta fina y temblorosa."""
        f = self._filtro("tinta", d, 10 + ancho)
        self.capas.append(("linea", '<path d="%s" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round" stroke-linejoin="round" opacity="%.2f" filter="url(#%s)"/>' % (d, color, ancho, opacidad, f)))

    def punto(self, cx, cy, r, color=TINTA, opacidad=0.9):
        d = "M%.1f %.1f L%.1f %.1f" % (cx - r, cy - r, cx + r, cy + r)
        f = self._filtro("tinta", d, 10 + r)
        self.capas.append(("linea", '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity="%.2f" filter="url(#%s)"/>' % (cx, cy, r, color, opacidad, f)))

    def texto(self, x, y, s, tam=20, rot=0, color=TINTA):
        self.capas.append(("linea", '<text x="%.1f" y="%.1f" font-family="Covered By Your Grace, cursive" font-size="%d" fill="%s" opacity=".85" transform="rotate(%.1f %.1f %.1f)">%s</text>' % (x, y, tam, color, rot, x, y, s)))

    # ---------- agrupar (girar un objeto entero) ----------
    def grupo(self, rot=0.0, cx=0.0, cy=0.0, esc=1.0):
        return _Grupo(self, rot, cx, cy, esc)

    # ---------- salida ----------
    def svg(self, fondo=True, fuente_css=None):
        """SVG completo: primero todas las manchas (multiplicándose entre sí) y encima la tinta."""
        fuente_css = fuente_embebida() if fuente_css is None else fuente_css
        manchas = "".join('<g style="mix-blend-mode:multiply">%s</g>' % s for t, s in self.capas if t == "mancha")
        lineas = "".join(s for t, s in self.capas if t == "linea")
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
                '<defs><style>%s</style>%s</defs>%s%s<g style="mix-blend-mode:multiply">%s</g></svg>'
                % (self.w, self.h, self.w, self.h, fuente_css, "".join(self.filtros),
                   '<rect width="100%" height="100%" fill="#fff"/>' if fondo else '', manchas, lineas))


# Filtros SVG con región propia (userSpaceOnUse: así valen también para líneas rectas, cuya caja mide cero de alto):
#   «wcb» cuerpo de la acuarela · «wcr» borde de pigmento · «tinta» línea temblorosa.
# Las modulaciones (densidad, grano, borde) se hacen SOLO sobre el alfa y se aplican al color con «in»:
# mezclar con «arithmetic» imágenes con color oscurecería los tonos y los dejaría sucios.
FILTRO = {
    "wcb": '''<filter id="{id}" filterUnits="userSpaceOnUse" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="{s:.3f}" numOctaves="3" seed="7" result="ruidoBorde"/>
  <feDisplacementMap in="SourceGraphic" in2="ruidoBorde" scale="14" xChannelSelector="R" yChannelSelector="G" result="deformada"/>
  <feGaussianBlur in="deformada" stdDeviation="0.9" result="color"/>
  <feColorMatrix in="color" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="forma"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" seed="21" result="ruidoDensidad"/>
  <feColorMatrix in="ruidoDensidad" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.9 0 0 0 0.45" result="densidad"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="papel"/>
  <feColorMatrix in="papel" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.9 0 0 0 0.62" result="grano"/>
  <feComposite in="forma" in2="densidad" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="m1"/>
  <feComposite in="m1" in2="grano" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="mascara"/>
  <feComposite in="color" in2="mascara" operator="in"/>
</filter>''',
    "wcr": '''<filter id="{id}" filterUnits="userSpaceOnUse" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="{s:.3f}" numOctaves="3" seed="7" result="ruidoBorde"/>
  <feDisplacementMap in="SourceGraphic" in2="ruidoBorde" scale="14" xChannelSelector="R" yChannelSelector="G" result="deformada"/>
  <feGaussianBlur in="deformada" stdDeviation="0.9" result="color"/>
  <feColorMatrix in="color" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="forma"/>
  <feGaussianBlur in="forma" stdDeviation="5" result="difusa"/>
  <feComposite in="forma" in2="difusa" operator="arithmetic" k1="0" k2="2.8" k3="-2.8" k4="0" result="borde"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="5" result="ruidoBorde2"/>
  <feColorMatrix in="ruidoBorde2" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.2 0 0 0 0.25" result="irregular"/>
  <feComposite in="borde" in2="irregular" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="mascara"/>
  <feComposite in="color" in2="mascara" operator="in"/>
</filter>''',
    "tinta": '''<filter id="{id}" filterUnits="userSpaceOnUse" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}">
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="11" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="3.2" xChannelSelector="R" yChannelSelector="G"/>
</filter>''',
}
