"""Alfabeto de rotulista: mayúsculas de UN SOLO TRAZO por golpe de pincel.

Cada letra es una lista de trazos en el orden y el sentido en que los pinta un rotulista
(verticales de arriba abajo, horizontales de izquierda a derecha, curvas desde arriba a la
derecha en sentido antihorario). Coordenadas en «unidades de mayúscula»: y = 0 arriba de la
letra, y = 1 en la línea base (hacia abajo, como en SVG); x desde el borde izquierdo de la letra.
Letras condensadas (avance ≈ 0,62 de la altura) para que los títulos largos quepan en el móvil.

Trazo = (tipo, puntos, opciones)
  tipo   'c' curva suave que pasa por los puntos (Catmull-Rom) · 'l' segmento recto
  opciones (dict, puede faltar):
    cerrado  el trazo vuelve cerca de su principio: se acorta un poco al final para que
             «no cierre del todo» (O, D, B, P, R)
    pasa     travesaño que se pasa de largo un poco (A, E, F, T, G)
    punto    golpe corto de pincel (puntos de ¡ ! . ·)
"""

C, L = 'c', 'l'
CERR = {'cerrado': True}
PASA = {'pasa': True}
PUNTO = {'punto': True}

# (avance, [trazos])
LETRAS = {
    'A': (0.62, [
        (L, [(0.31, 0.0), (0.04, 1.0)], {}),
        (L, [(0.31, 0.0), (0.58, 1.0)], {}),
        (L, [(0.15, 0.66), (0.49, 0.65)], PASA),
    ]),
    'B': (0.55, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (C, [(0.08, 0.02), (0.32, 0.0), (0.46, 0.1), (0.46, 0.31), (0.3, 0.46), (0.1, 0.48)], CERR),
        (C, [(0.12, 0.47), (0.37, 0.48), (0.52, 0.61), (0.52, 0.83), (0.36, 0.98), (0.08, 0.99)], CERR),
    ]),
    'C': (0.56, [
        (C, [(0.53, 0.17), (0.41, 0.03), (0.25, 0.02), (0.1, 0.17), (0.04, 0.5), (0.1, 0.83),
             (0.26, 0.98), (0.42, 0.97), (0.54, 0.84)], {}),
    ]),
    'D': (0.58, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (C, [(0.08, 0.02), (0.29, 0.02), (0.48, 0.14), (0.56, 0.5), (0.49, 0.85), (0.29, 0.98), (0.09, 0.99)], CERR),
    ]),
    'E': (0.5, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (L, [(0.08, 0.02), (0.46, 0.0)], PASA),
        (L, [(0.08, 0.49), (0.39, 0.48)], PASA),
        (L, [(0.08, 0.99), (0.48, 0.98)], PASA),
    ]),
    'F': (0.48, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (L, [(0.08, 0.02), (0.46, 0.0)], PASA),
        (L, [(0.08, 0.5), (0.38, 0.49)], PASA),
    ]),
    'G': (0.6, [
        (C, [(0.54, 0.17), (0.42, 0.03), (0.26, 0.02), (0.1, 0.17), (0.04, 0.5), (0.1, 0.83),
             (0.27, 0.98), (0.45, 0.96), (0.56, 0.8), (0.56, 0.6)], {}),
        (L, [(0.35, 0.59), (0.58, 0.58)], PASA),
    ]),
    'I': (0.22, [
        (L, [(0.11, 0.0), (0.11, 1.0)], {}),
    ]),
    'J': (0.46, [
        (C, [(0.38, 0.0), (0.38, 0.4), (0.37, 0.72), (0.3, 0.93), (0.16, 0.98), (0.04, 0.86)], {}),
    ]),
    'L': (0.46, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (L, [(0.08, 0.99), (0.44, 0.97)], PASA),
    ]),
    'M': (0.74, [
        (L, [(0.08, 0.0), (0.06, 1.0)], {}),
        (L, [(0.08, 0.0), (0.37, 0.64)], {}),
        (L, [(0.37, 0.64), (0.66, 0.0)], {}),
        (L, [(0.66, 0.0), (0.69, 1.0)], {}),
    ]),
    'N': (0.6, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (L, [(0.08, 0.0), (0.52, 1.0)], {}),
        (L, [(0.53, 0.0), (0.53, 1.0)], {}),
    ]),
    'O': (0.62, [
        (C, [(0.33, 0.02), (0.13, 0.12), (0.04, 0.48), (0.12, 0.86), (0.32, 0.98), (0.52, 0.86),
             (0.59, 0.48), (0.52, 0.13), (0.36, 0.03)], CERR),
    ]),
    'P': (0.52, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (C, [(0.08, 0.02), (0.31, 0.0), (0.47, 0.11), (0.48, 0.32), (0.33, 0.5), (0.1, 0.52)], CERR),
    ]),
    'R': (0.56, [
        (L, [(0.08, 0.0), (0.08, 1.0)], {}),
        (C, [(0.08, 0.02), (0.31, 0.0), (0.47, 0.11), (0.48, 0.32), (0.33, 0.5), (0.1, 0.52)], CERR),
        (L, [(0.25, 0.52), (0.54, 1.0)], {}),
    ]),
    'S': (0.52, [
        (C, [(0.48, 0.13), (0.36, 0.02), (0.18, 0.03), (0.06, 0.16), (0.08, 0.33), (0.26, 0.46),
             (0.42, 0.56), (0.5, 0.73), (0.44, 0.92), (0.26, 0.99), (0.1, 0.95), (0.03, 0.84)], {}),
    ]),
    'T': (0.56, [
        (L, [(0.02, 0.03), (0.54, 0.0)], PASA),
        (L, [(0.28, 0.02), (0.28, 1.0)], {}),
    ]),
    'U': (0.58, [
        (C, [(0.07, 0.0), (0.07, 0.4), (0.08, 0.72), (0.15, 0.92), (0.29, 0.99), (0.43, 0.92),
             (0.5, 0.72), (0.51, 0.4), (0.51, 0.0)], {}),
    ]),
    'Y': (0.58, [
        (L, [(0.04, 0.0), (0.29, 0.52)], {}),
        (L, [(0.54, 0.0), (0.29, 0.52)], {}),
        (L, [(0.29, 0.5), (0.29, 1.0)], {}),
    ]),
    '¡': (0.24, [
        (L, [(0.12, 0.04), (0.12, 0.08)], PUNTO),
        (L, [(0.12, 0.32), (0.12, 1.14)], {}),
    ]),
    '!': (0.24, [
        (L, [(0.12, 0.0), (0.12, 0.7)], {}),
        (L, [(0.12, 0.93), (0.12, 0.97)], PUNTO),
    ]),
    '.': (0.2, [
        (L, [(0.1, 0.93), (0.1, 0.97)], PUNTO),
    ]),
    '·': (0.26, [
        (L, [(0.13, 0.48), (0.13, 0.52)], PUNTO),
    ]),
    ' ': (0.3, []),
}

# Vocales con tilde: la letra base y el acento encima (trazo corto, de abajo a la izquierda hacia arriba a la derecha)
ACENTO = (L, [(0.27, -0.1), (0.41, -0.27)], {})
for _con, _sin in (('Ó', 'O'), ('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ú', 'U')):
    _av, _tr = LETRAS[_sin]
    _dx = _av / 2 - 0.34
    _ac = (ACENTO[0], [(x + _dx, y) for x, y in ACENTO[1]], ACENTO[2])
    LETRAS[_con] = (_av, _tr + [_ac])


def letra(c):
    """(avance, trazos) de un carácter; las minúsculas se rotulan como mayúsculas."""
    c = c.upper()
    if c not in LETRAS:
        raise KeyError(f'Falta la letra «{c}» en scripts/rotulos/alfabeto.py')
    return LETRAS[c]
