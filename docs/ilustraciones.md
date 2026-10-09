# Ilustraciones · Marta y Jorge

> **Nota de ubicación:** esta guía vive en `docs/` para no publicarse con la web. Las variantes solo tinta (`san-pablo-linea.svg`, `palomar-linea.svg`) están en `docs/ilustraciones/` por la misma razón; las ilustraciones que usa la web están en `public/assets/ilustraciones/`.

Hay **dos familias** de dibujos:

1. **A pluma** (este documento, §1 en adelante): San Pablo, el Palomar, la ruta con el corazón, adornos, iconos y favicon. SVG vectorial.
2. **De acuarela** (§0, justo debajo): la guirnalda y la mesa puesta entre la portada y la Agenda, el ramo con las alianzas, la
   almohada con la llave, la maleta y las granadas del pie. Se dibujan con código y se publican como WebP con transparencia.


## 0. Acuarelas (`public/assets/ilustraciones/acuarela/*.webp`)

Son dibujos **propios**, hechos con código (no están calcados ni copiados de ninguna otra web): la misma idea —una mesa puesta, una
boda, un viaje— con trazo propio. Cada objeto (tomate, vela, copa, gerbera, maleta…) se compone de manchas de color con el borde
irregular y el pigmento acumulado en el contorno (filtros SVG: desplazamiento, desenfoque, granulado de papel) y unas líneas de tinta
finas y algo temblorosas, ligeramente «desregistradas» como en una ilustración impresa.

| Fichero | Dónde sale | Tamaños |
|---|---|---|
| `guirnalda-630.webp` | tira de banderines que se repite a todo el ancho, sobre la mesa puesta | 630 px (se muestra a 180–300 px) |
| `bodegon-640/1000.webp` | mesa puesta: narcisos, vela, copa, gerberas, botella, tomates… (entre la portada y la Agenda) | 640 y 1000 px |
| `ramo-480/760.webp` | ramo de flores rojas con las alianzas (final de la Agenda) | 480 y 760 px |
| `almohada-460/700.webp` | almohada y llave de habitación (Alojamiento) | 460 y 700 px |
| `maleta-380/560.webp` | maleta antigua con etiqueta «luna de miel» (Lista de bodas) | 380 y 560 px |
| `granadas-300/420.webp` | dos granadas con hojas (pie de página) | 300 y 420 px |

- **Regenerar**: `python3 scripts/acuarela/generar.py` (necesita Pillow, Node con Playwright y Chromium; variables
  `PLAYWRIGHT_PATH` y `CHROME_PATH` si no están instalados globalmente). Es determinista: salen siempre las mismas imágenes.
  Dibuja cada escena de `escenas.py` como SVG, Chromium lo convierte en PNG transparente (`exportar.cjs`) y Pillow lo guarda como WebP.
- **Retocar**: los objetos están en `scripts/acuarela/objetos.py` (`tomate`, `vela`, `copa`, `gerbera`, `maleta`…) y su
  composición en `scripts/acuarela/escenas.py` (posiciones y tamaños, en unidades de lienzo). Los colores salen de `PAL`.
  La librería de acuarela (manchas, filtros, líneas) está en `lib.py`.
- **Calidad y peso**: se guardan con calidad 66 y alfa 62 (`generar.py`): pesan la mitad que con 82/90 y no se nota. Con los tamaños
  pequeños, un móvil se descarga unos 100 KB de acuarelas en total, y todas se piden solo al acercarse (`loading="lazy"`).
- Son **decorativas** (`alt=""` y `aria-hidden`): no cuentan nada que no esté ya en el texto.
- El fondo de lino con rayas **no** es una acuarela: la textura (`public/assets/img/lino.webp`) sale de `scripts/fondo/generar.py` y
  las rayas rosas son un degradado CSS en `base.css` (`--rosa`, `--p`).

---

## A pluma (resto del documento)

Dibujos a pluma propios (no calcados): San Pablo, el Palomar, la ruta con el corazón y el
avioncito, adornos, iconos y favicon. Todo es SVG vectorial, transparente, sin `<text>`, sin
imágenes incrustadas, sin `<filter>` y solo con `viewBox` (sin width/height).

- **Regenerar** (determinista, mismas semillas → mismos SVG):
  `python3 scripts/ilustraciones/generar.py` (o `… generar.py san_pablo palomar rutas adornos iconos favicon`).
  Solo usa la biblioteca estándar de Python 3. El motor del trazo está en `scripts/ilustraciones/pluma.py`.
- **Tinta**: `#4b3c37` (marrón grisáceo oscuro, `TINTA` en `pluma.py`) fija en las ilustraciones grandes; rojo `#a3121d` (`ROJO`) en la ruta, el avión y el favicon; `currentColor` en los sprites.
- **Aguadas**: ocre `#c3a063` (piedra/revoco), terracota `#a4563a` (teja, ladrillo, puerta), oliva
  `#6c7550` (árboles, césped), con poca opacidad y desplazadas 2–4 unidades del trazo (desregistro).

| Fichero | viewBox | Peso |
|---|---|---|
| `san-pablo.svg` / `san-pablo-linea.svg` | `0 0 520 620` | 59 / 56 KB |
| `palomar.svg` / `palomar-linea.svg` | `0 0 700 440` | 51 / 48 KB |
| `ruta-horizontal.svg` | `0 0 480 150` | 1,2 KB |
| `ruta-vertical.svg` | `0 0 170 560` | 1,3 KB |
| `adornos.svg` (sprite) | por símbolo | 4 KB |
| `iconos.svg` (sprite) | `0 0 48 48` | 5 KB |
| `favicon.svg` | `0 0 64 64` | 0,6 KB |

Recomendación: usar las versiones **con aguada** (`san-pablo.svg`, `palomar.svg`); las `-linea.svg`
son la misma línea sin color, por si se prefiere un acabado solo a tinta.

---

## 1. `san-pablo.svg` y `palomar.svg` (Agenda)

Estructura (idéntica en ambos y en sus versiones `-linea`):

```
<svg viewBox="…">
  <g class="color" stroke="none"> …manchas de aguada (path con fill y fill-opacity)… </g>   (falta en -linea)
  <g class="linea" fill="none" stroke="#4b3c37" stroke-linecap="round" stroke-linejoin="round">
    <g stroke-width="2.2"> <path class="l" pathLength="1" d="…"/> … </g>    contornos (2,2–2,4)
    <g stroke-width="1.2"> … </g>                                             detalles (1,2–1,4)
    <g stroke-width=".8">  … </g>                                             sombreado (0,8–1)
  </g>
</svg>
```

- Cada trazo es su propio `<path class="l" pathLength="1">`. El orden del DOM es el de dibujo:
  primero contornos, luego detalles y al final sombreado.
- **Texturas**: cada zona de rayado (sombras, sillería, ladrillo, tejas, césped) es UN `path.l` con
  varios subtrazos (`M…m…`). Así pesan mucho menos. Con la animación se dibujan todas las rayitas
  a la vez (el patrón de guiones se reinicia en cada subtrazo) y el estado final es idéntico.
- El Palomar lleva a los novios paseando (ella con velo largo, él de traje oscuro) y tres palomas.
  Si se prefiere sin figuras: en `scripts/ilustraciones/generar.py` usar `palomar.dibujar(con_novios=False)`;
  las palomas son las tres llamadas a `paloma()` de `palomar.py`.
- Textos alternativos sugeridos (si no son decorativas): «Fachada de la Iglesia de San Pablo de
  Valladolid, dibujada a pluma» y «El Palomar de La Posada Real del Pinar entre pinos, dibujado a pluma».

### Uso estático
`<img src="assets/ilustraciones/san-pablo.svg" alt="" width="520" height="620">`. Funciona tal cual, pero
el CSS de la página no puede animar lo que hay dentro de un `<img>`.

### Animación «se dibuja sola» (SVG en línea)

> **Importante:** con `stroke-dasharray: 1` + `stroke-dashoffset: 1` y `stroke-linecap: round`,
> Chromium deja **puntitos sueltos** en el estado inicial (comprobado: 235 píxeles de tinta en la
> captura «vacía»). Solución: `stroke-dasharray: 1 2` (el hueco es mayor que el trazo). Con eso,
> 0 puntitos y el final es idéntico. No hace falta cambiar a `butt`.

HTML (el `<img>` es el respaldo sin JS; el JS lo sustituye por el SVG en línea):

```html
<figure class="ilustracion" data-svg="assets/ilustraciones/san-pablo.svg">
  <img src="assets/ilustraciones/san-pablo.svg" alt="" width="520" height="620" decoding="async">
</figure>
<!-- … -->
<figure class="ilustracion" data-svg="assets/ilustraciones/palomar.svg">
  <img src="assets/ilustraciones/palomar.svg" alt="" width="700" height="440" decoding="async">
</figure>
```

CSS:

```css
.ilustracion svg, .ilustracion img { display: block; width: 100%; height: auto; }
.ilustracion .linea .l {
  stroke-dasharray: 1 2;            /* ¡no «1»! (puntitos) */
  stroke-dashoffset: 1;
  transition: stroke-dashoffset 2.2s cubic-bezier(.22, .61, .36, 1) var(--retraso, 0s);
}
.ilustracion.dibujada .linea .l, .reveal-fallback .ilustracion .linea .l { stroke-dashoffset: 0; }
.ilustracion .color { opacity: 0; transition: opacity 1.4s ease 1.6s; }
.ilustracion.dibujada .color, .reveal-fallback .ilustracion .color { opacity: 1; }
@media (prefers-reduced-motion: reduce) {
  .ilustracion .linea .l { stroke-dasharray: none; stroke-dashoffset: 0; transition: none; }
  .ilustracion .color { opacity: 1; transition: none; }
}
```

JS (vanilla, sin dependencias):

```js
async function incrustarSVG(el) {
  const res = await fetch(el.dataset.svg);
  if (!res.ok) return null;                    // se queda el <img>
  el.innerHTML = await res.text();
  const svg = el.querySelector('svg');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  return svg;
}

const io = new IntersectionObserver((entradas) => {
  for (const e of entradas) if (e.isIntersecting) { e.target.classList.add('dibujada'); io.unobserve(e.target); }
}, { threshold: 0.25 });

document.querySelectorAll('.ilustracion[data-svg]').forEach(async (fig) => {
  const svg = await incrustarSVG(fig);
  if (!svg) return;
  const trazos = svg.querySelectorAll('.linea .l');
  trazos.forEach((p, i) => p.style.setProperty('--retraso', (i / trazos.length * 1.3).toFixed(2) + 's'));
  svg.getBoundingClientRect();                 // fija el estado inicial antes de animar
  io.observe(fig);
});
```

(Si se prefiere no incrustar: `<img>` y un simple fundido; el dibujo se ve igual.)

---

## 2. `ruta-horizontal.svg` y `ruta-vertical.svg`

- `<path id="ruta">`: UN trazo continuo, sin subtrazos ni `pathLength`. Lleva
  `stroke-dasharray="9 6.5 7 7 10.5 6 6.5 7.5 8 6"` (guiones irregulares, a mano) y tinta.
  Va de la iglesia al palomar (izquierda → derecha / arriba → abajo) y hace un lazo en forma de corazón
  hacia el primer tercio (entra por la punta, se cruza consigo mismo y sale).
  `getTotalLength()` ≈ 700 (horizontal) y ≈ 856 (vertical) unidades. La horizontal está dibujada para
  verse a ~260–420 px (columna central de la agenda): guiones, corazón y avión a esa escala; trazo 2,4
  (la vertical, 2,1).
- `<g id="avion">`: avión de papel **centrado en (0,0), morro hacia +X, sin transform**, de
  ~30 × 18 unidades, con relleno crema claro (`#fbf8f1`) que tapa los guiones que tenga debajo.
  ⚠️ Mientras el JS no lo coloque, se ve en la esquina (0,0) recortado; por eso la ruta debe ir en
  línea y colocarse al cargar (`colocar(0)` en el código de abajo). Como `<img>`, mejor no usarla.
- Los extremos de la ruta dejan ~18 unidades de margen para que el morro no se salga del viewBox.
- Si conviven las dos rutas en el DOM (una oculta por CSS), los ids se repiten: usar
  `contenedor.querySelector('#ruta')` (no `getElementById`).
- Color: sale ya en rojo (`#a3121d`); `#ruta { stroke: var(--rojo) }` funciona si va en línea (el CSS gana al atributo).

HTML (las dos; el CSS de la web muestra una u otra):

```html
<div class="ruta ruta--h" data-svg="assets/ilustraciones/ruta-horizontal.svg" aria-hidden="true"></div>
<div class="ruta ruta--v" data-svg="assets/ilustraciones/ruta-vertical.svg" aria-hidden="true"></div>
```

```css
.ruta svg { display: block; width: 100%; height: auto; }
.ruta--v { display: none; }
@media (max-width: 47.99em) { .ruta--h { display: none; } .ruta--v { display: block; max-width: 7.5rem; margin-inline: auto; } }
```

JS (usa `incrustarSVG` de arriba): coloca el avión, revela la ruta tras él con una máscara y lo hace volar
siguiendo la tangente.

```js
function volarAvion(svg, ms = 3200) {
  const NS = 'http://www.w3.org/2000/svg';
  const ruta = svg.querySelector('#ruta'), avion = svg.querySelector('#avion');
  const L = ruta.getTotalLength();
  // máscara: un trazo sólido (sin guiones) que crece; muestra la ruta discontinua solo hasta el avión
  const id = 'ruta-m-' + Math.random().toString(36).slice(2, 8);
  const mascara = document.createElementNS(NS, 'mask');
  const vb = svg.viewBox.baseVal;
  mascara.setAttribute('id', id);
  mascara.setAttribute('maskUnits', 'userSpaceOnUse');
  mascara.setAttribute('x', vb.x - 20); mascara.setAttribute('y', vb.y - 20);
  mascara.setAttribute('width', vb.width + 40); mascara.setAttribute('height', vb.height + 40);
  const trazo = ruta.cloneNode();
  trazo.removeAttribute('id');
  trazo.setAttribute('stroke', '#fff'); trazo.setAttribute('stroke-width', '10');
  trazo.setAttribute('stroke-linecap', 'butt');
  trazo.setAttribute('stroke-dasharray', `${L} ${L}`);
  mascara.append(trazo);
  svg.prepend(mascara);
  ruta.setAttribute('mask', `url(#${id})`);

  const colocar = (s) => {
    const p = ruta.getPointAtLength(s);
    const a = ruta.getPointAtLength(Math.max(0, s - 1)), b = ruta.getPointAtLength(Math.min(L, s + 1));
    const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
    avion.setAttribute('transform', `translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) rotate(${ang.toFixed(1)})`);
    trazo.setAttribute('stroke-dashoffset', (L - s).toFixed(1));
  };
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { colocar(L); return; }
  colocar(0);
  const io = new IntersectionObserver(([e]) => {
    if (!e.isIntersecting) return;
    io.disconnect();
    const t0 = performance.now();
    requestAnimationFrame(function paso(t) {
      const f = Math.min(1, (t - t0) / ms);
      const k = f < 0.5 ? 4 * f * f * f : 1 - Math.pow(-2 * f + 2, 3) / 2;   // easeInOutCubic
      colocar(k * L);
      if (f < 1) requestAnimationFrame(paso);
    });
  }, { threshold: 0.4 });
  io.observe(svg);
}

document.querySelectorAll('.ruta[data-svg]').forEach(async (el) => {
  const svg = await incrustarSVG(el);
  if (svg) volarAvion(svg);
});
```

(La ruta oculta con `display:none` nunca entra en pantalla, así que no se anima.)

---

## 3. `adornos.svg` (sprite, `currentColor`)

| id | viewBox | qué es |
|---|---|---|
| `floritura` | `0 0 160 32` | línea ondulada fina con rombo y punto central (como la de la invitación) |
| `floritura-corta` | `0 0 96 24` | versión corta |
| `corazon` | `0 0 48 44` | corazón a pluma (dos trazos que se cruzan en la punta) |
| `ramita` | `0 0 120 48` | ramita de olivo con dos aceitunas |

Los trazos también son `path.l` con `pathLength="1"`. Como `stroke-dasharray` y `stroke-dashoffset`
se heredan, se pueden animar desde el `<svg>` contenedor aunque vayan por `<use>`.

```html
<svg class="adorno" viewBox="0 0 160 32" aria-hidden="true" focusable="false">
  <use href="assets/ilustraciones/adornos.svg#floritura"/>
</svg>
<svg class="adorno adorno--corazon" viewBox="0 0 48 44" aria-hidden="true" focusable="false">
  <use href="assets/ilustraciones/adornos.svg#corazon"/>
</svg>
```

```css
.adorno { display: block; width: min(10rem, 60%); height: auto; margin-inline: auto; color: var(--tinta); }
.adorno--corazon { width: 2.25rem; color: var(--terracota); }
/* Opcional: que «se dibuje» al revelarse. Añadir la clase .revelar al <svg class="adorno">
   (main.js le pone .visible al entrar en pantalla; .reveal-fallback lo muestra si main.js falla). */
.js .adorno.revelar {
  stroke-dasharray: 1 2; stroke-dashoffset: 1;
  transition: opacity .9s var(--ease), transform .9s var(--ease), stroke-dashoffset 1.8s var(--ease);
}
.js .adorno.revelar.visible, .reveal-fallback .adorno.revelar { stroke-dashoffset: 0; }
@media (prefers-reduced-motion: reduce) { .js .adorno.revelar { stroke-dashoffset: 0; } }
```

---

## 4. `iconos.svg` (sprite, rejilla 48×48, `currentColor`, trazo 2)

Ids: `coche`, `autocar`, `cama`, `pin`, `regalo`, `maleta`, `copiar`, `check`, `flecha-abajo`,
`corazon`, `avion`, `anillos`. Cada `<symbol>` ya trae `viewBox="0 0 48 48"`, `fill="none"`,
`stroke="currentColor"`, `stroke-width="2"` y extremos redondeados. Se leen bien de 20 a 48 px.

```html
<svg class="icono" viewBox="0 0 48 48" width="32" height="32" aria-hidden="true" focusable="false">
  <use href="assets/ilustraciones/iconos.svg#coche"/>
</svg>
```

(Para un botón «Copiar» con cambio a «check», se cambia el `href` del `<use>`.)

Nota: `corazon` existe en `adornos.svg` y en `iconos.svg`; como se referencian como ficheros externos
no chocan. Si algún día se pegan los dos sprites dentro del HTML, hay que renombrar uno de ellos.
Los sprites externos con `<use>` necesitan servirse por http(s) (no `file://`).

---

## 5. `favicon.svg`

Lazo en forma de corazón (el de la ruta) con la punta del avión, de trazo grueso para que se lea a
16 px. Rojo `#a3121d` sobre transparente; con `prefers-color-scheme: dark` pasa a rosa claro para no
desaparecer en pestañas oscuras.

```html
<link rel="icon" href="assets/ilustraciones/favicon.svg" type="image/svg+xml">
```

(Safari antiguo no usa favicons SVG; si hiciera falta, exportar un PNG de 180 px para `apple-touch-icon`.)
