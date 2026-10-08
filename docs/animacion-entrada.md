# Animación de entrada de la portada

Está pensada como una invitación hecha a mano: **papel, tinta y un poco de magia**. Nada de destellos ni
rebotes; todo es lento, suave y se puede saltar en cualquier momento.

## Qué se ve (≈ 5 s)

| t (s) | Qué pasa |
|---|---|
| 0,2 – 2,3 | Un avión de papel cruza la parte alta dejando su estela de rayas terracota y hace un lazo en forma de corazón (la misma ruta que luego recorre en la Agenda) |
| 0,75 | «¡Nos casamos!» aparece con un fundido suave |
| 0,85 – 3,7 | **«Marta y Jorge» se escriben a pluma**, trazo a trazo y en el orden en que se escribe cada letra (la M en un zigzag, la J de arriba abajo, el travesaño de la t al final…). La «y», en terracota |
| 1,2 – 2,8 | Se dibujan a línea las **puertas en arco** (contorno, costura, marcos y pomos) y después se rellenan de papel |
| 3,0 – 4,5 | Las puertas **se abren en 3D**, con su sombra, y la foto aparece «enfocándose» (de borrosa a nítida, con un leve acercamiento) |
| 3,5 – 4,6 | Fecha, cuenta atrás y botón entran con un fundido |
| después | La foto «respira» (≈ 3 % de zoom en 32 s) y las capas tienen un parallax muy sutil con el scroll y, en escritorio, con el ratón |

## Cómo está hecha

- **CSS puro**: [`public/css/intro.css`](../public/css/intro.css). Todas las animaciones son de tipo «desde»:
  el estado normal de cada elemento es el **final**. Por eso, sin animaciones la portada sale completa al instante.
- **Se salta**: si la persona hace scroll, toca o pulsa una tecla durante la entrada, todo se acelera ×7 y termina
  en menos de un segundo ([`public/js/intro.js`](../public/js/intro.js)).
- **Solo la primera vez por sesión**: al recargar o volver a abrir la página en la misma pestaña, la portada sale
  completa sin repetir ([`public/js/boot.js`](../public/js/boot.js)).
  - `?intro=1` en la dirección fuerza que se vea otra vez (útil para enseñarla): `https://tu-dominio/?intro=1`.
  - `?intro=0` la omite.
- **Accesibilidad**: con «reducir movimiento» activado en el sistema no hay animación (portada completa
  al instante) y tampoco parallax. Los nombres siguen siendo texto para lectores de pantalla (`<h1>` con el texto
  «Marta y Jorge»; el SVG va oculto para ellos).
- **Sin JavaScript** la entrada también se reproduce (es CSS); solo se pierden el avance rápido y el parallax.

## Retocarla

| Quiero… | Dónde |
|---|---|
| Que empiece antes/después una fase | variables `--escritura`, `--lineas`, `--abre` al principio de `intro.css` |
| Que fecha/cuenta atrás/botón entren antes o después | `style="--d:…"` de esos elementos en `public/index.html` |
| Escribir los nombres más rápido o despacio | `VELOCIDAD=9000 scripts/intro/generar.sh` (por defecto 7600 unidades/s) y volver a pegar el SVG |
| Quitar la foto «respirando» | borrar `respira …` de `.ventana img` en `intro.css` |
| Desactivar toda la entrada | añadir la clase `intro-vista` a `<html>` en `index.html` (o quitar el `<link>` a `intro.css`) |

## Las dos piezas generadas

Los nombres escritos y el ornamento no están dibujados a mano: salen de scripts reproducibles en
[`scripts/intro/`](../scripts/intro/).

1. **Nombres** (`glifos.py` → `trazos.py` → `ensamblar.py` → `svg.py`): se toma la Caveat en peso 700, se calcula el
   **esqueleto** de cada letra, se convierte en trazos de pluma ordenados (con sentido de escritura, ápices y
   extremos cubiertos) y se emite un SVG donde cada trazo grueso, **recortado por el contorno real de la letra**
   (`clipPath`), se «dibuja» con `stroke-dashoffset`. Al terminar cada letra entra su relleno exacto, así que el
   resultado final es idéntico a la tipografía.
2. **Ornamento** (`ornamento.cjs`): muestrea la ruta de la ilustradora, parte la línea en sus 48 rayas, hace que
   cada una aparezca en la estela del avión y genera los 56 fotogramas CSS del vuelo con **la misma curva de
   easing**, para que avión y rayas vayan perfectamente sincronizados sin JavaScript.

Para regenerarlas: `scripts/intro/generar.sh` (necesita Python con `numpy scikit-image fonttools brotli uharfbuzz pillow`
y Node con Playwright; ver cabecera del script). Deja los resultados en `scripts/intro/.tmp/` con las instrucciones
de dónde pegarlos.

## Probarla fotograma a fotograma

En la consola del navegador (con `?intro=1`), para congelar la animación en el segundo 3,2:

```js
document.getAnimations().forEach(a => { a.pause(); a.currentTime = 3200; });
```

## Qué no se ha podido probar

La entrada se ha comprobado en Chromium (móvil y escritorio, con CPU 4× más lenta, sin JS, con movimiento
reducido, segunda visita y avance rápido). **No** se ha probado en Safari/iOS ni Firefox reales; todo lo que usa
es estándar (CSS animations, `clipPath`, `stroke-dashoffset`, transformaciones 3D, `getAnimations`), con
alternativas en los casos dudosos, pero conviene mirarla en un iPhone antes de repartir la invitación.
