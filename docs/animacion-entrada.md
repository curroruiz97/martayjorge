# Animación de entrada de la portada

Está pensada como una invitación hecha a mano: **papel, tinta y un poco de magia**. Nada de destellos ni
rebotes; todo es lento, suave y se puede saltar en cualquier momento.

## Qué se ve (≈ 5 s)

| t (s) | Qué pasa |
|---|---|
| 0,2 – 2,3 | Un avión de papel cruza la parte alta dejando su estela de rayas terracota y hace un lazo en forma de corazón (la misma ruta que luego recorre en la Agenda) |
| 0,75 | «¡Nos casamos!» aparece con un fundido suave |
| 0,85 – 4,0 | **«Marta y Jorge» se escriben a pluma** con una caligrafía fina (Corinthia), trazo a trazo y en el orden en que se escribe cada letra (la M empieza por su lazo, la J baja y cierra en un bucle…). La «y», en terracota |
| 1,2 – 2,8 | Se dibujan a línea las **puertas en arco** (contorno, costura, marcos y pomos) y después se rellenan de papel |
| 3,0 – 4,5 | Las puertas **se abren en 3D**, con su sombra, y la foto aparece «enfocándose» (de borrosa a nítida, con un leve acercamiento) |
| 3,5 – 4,6 | Fecha, cuenta atrás y botón entran con un fundido |
| después | La foto «respira» (≈ 3 % de zoom en 32 s), las capas tienen un parallax muy sutil con el scroll y, en escritorio, con el ratón, y aparece una pista discreta (una línea con un punto que baja) para seguir bajando |

## Cómo está hecha

- **CSS puro**: [`public/css/intro.css`](../public/css/intro.css). Todas las animaciones son de tipo «desde»:
  el estado normal de cada elemento es el **final**. Por eso, sin animaciones la portada sale completa al instante.
- **Se salta**: si la persona hace scroll, toca o pulsa una tecla durante la entrada, todo se acelera ×7 y termina
  en menos de un segundo ([`public/js/intro.js`](../public/js/intro.js)).
- **Se reproduce siempre**, en cada carga de la página ([`public/js/boot.js`](../public/js/boot.js)): quien abra el
  enlace —o recargue— la ve, y quien tenga prisa la acelera con un toque o un scroll. No hay memoria entre visitas.
  - `?intro=0` en la dirección la omite (portada completa al instante).
  - Si el enlace lleva un ancla (por ejemplo `https://tu-dominio/#confirmacion`) tampoco se reproduce, porque la persona
    aterriza directamente en esa parte de la página y la portada ni se ve.
- **Conexión lenta**: si a los 2,6 s la foto aún no ha llegado, las puertas esperan a que llegue (como mucho 9 s) en
  lugar de abrirse sobre un hueco vacío.
- **Accesibilidad**: con «reducir movimiento» activado en el sistema no hay animación (portada completa
  al instante) y tampoco parallax. Los nombres siguen siendo texto para lectores de pantalla (`<h1>` con el texto
  «Marta y Jorge»; el SVG va oculto para ellos).
- **Sin JavaScript** la entrada también se reproduce (es CSS); solo se pierden el avance rápido y el parallax.

## Retocarla

| Quiero… | Dónde |
|---|---|
| Que empiece antes/después una fase | variables `--escritura`, `--lineas`, `--abre` al principio de `intro.css` |
| Que fecha/cuenta atrás/botón entren antes o después | `style="--d:…"` de esos elementos en `public/index.html` |
| Escribir los nombres más rápido o despacio | `VELOCIDAD=12000 scripts/intro/generar.sh` (por defecto 10000 unidades/s) y volver a pegar el SVG |
| Cambiar la caligrafía de los nombres | poner otra fuente en `scripts/intro/` (ver abajo), ajustar las salidas de `trazos.py`/`ensamblar.py` y regenerar |
| Quitar la foto «respirando» | borrar `respira …` de `.ventana img` en `intro.css` |
| Quitar la pista para seguir bajando | borrar `<span class="portada__baja …">` de `public/index.html` |
| Desactivar toda la entrada | añadir la clase `intro-vista` a `<html>` en `index.html` (o quitar el `<link>` a `intro.css`) |

## Las dos piezas generadas

Los nombres escritos y el ornamento no están dibujados a mano: salen de scripts reproducibles en
[`scripts/intro/`](../scripts/intro/).

1. **Nombres** (`glifos.py` → `trazos.py` → `ensamblar.py` → `svg.py`): se toma la Corinthia
   (`public/assets/fonts/corinthia-latin-400-normal.woff2`, licencia OFL), se calcula el
   **esqueleto** de cada letra, se convierte en trazos de pluma ordenados (con sentido de escritura, ápices y
   extremos cubiertos) y se emite un SVG donde cada trazo grueso, **recortado por el contorno real de la letra**
   (`clipPath`), se «dibuja» con `stroke-dashoffset`. Al terminar cada letra entra su relleno exacto, así que el
   resultado final es idéntico a la tipografía. La composición (Marta arriba, la «y» pequeña y girada, Jorge
   recogido a la derecha) se calcula con las medidas reales de la tinta: se retoca en las constantes de `svg.py`
   (`ESCALA_Y`, `X_Y`, `HUECO_1`, `HUECO_2`, `SANGRIA_J`) o con variables de entorno del mismo nombre.
   Si se cambia de tipografía hay que revisar `debug_trazos.png` (en `.tmp/`: cada trazo va numerado y con su punto de
   partida) y ajustar `INICIO` en `trazos.py` e `INVERTIR` en `ensamblar.py`.
2. **Ornamento** (`ornamento.cjs`): muestrea la ruta de la ilustradora, parte la línea en sus 48 rayas, hace que
   cada una aparezca en la estela del avión y genera los 56 fotogramas CSS del vuelo con **la misma curva de
   easing**, para que avión y rayas vayan perfectamente sincronizados sin JavaScript.

Para regenerarlas: `scripts/intro/generar.sh` (necesita Python con `numpy scikit-image fonttools brotli uharfbuzz pillow`
y Node con Playwright; ver cabecera del script). Deja los resultados en `scripts/intro/.tmp/` con las instrucciones
de dónde pegarlos.

## Probarla fotograma a fotograma

En la consola del navegador (recién cargada la página), para congelar la animación en el segundo 3,2:

```js
document.getAnimations().forEach(a => { a.pause(); a.currentTime = 3200; });
```

## Rendimiento: lo que hay que saber

La entrada **no retrasa la carga real**: la primera pantalla aparece enseguida y la foto se descarga con prioridad
alta mientras se escriben los nombres. Mientras suena, no se descarga ni se procesa nada que esté más abajo
(las ilustraciones de la agenda esperan a que termine la entrada o a que la persona haga scroll).

Un detalle para quien mida con herramientas de laboratorio (PageSpeed, Lighthouse): la foto se revela a propósito
hacia los 3 s, así que en móvil con 4G lento simulado el «Largest Contentful Paint» sale hacia los 3,5 s y la
puntuación de rendimiento ronda 90 (en escritorio, 100; sin entrada, ≈ 93 en móvil). No es lentitud de carga:
la página está cargada y es usable desde el primer momento.

## Qué no se ha podido probar

La entrada se ha comprobado en Chromium (móvil y escritorio, con CPU 4× más lenta, sin JS, con movimiento
reducido, segunda visita y avance rápido). **No** se ha probado en Safari/iOS ni Firefox reales; todo lo que usa
es estándar (CSS animations, `clipPath`, `stroke-dashoffset`, transformaciones 3D, `getAnimations`), con
alternativas en los casos dudosos, pero conviene mirarla en un iPhone antes de repartir la invitación.
