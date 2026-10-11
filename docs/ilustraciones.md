# Ilustraciones · Marta y Jorge

> **Nota de ubicación:** esta guía vive en `docs/` para no publicarse con la web. Los dibujos a pluma de la V1
> (`san-pablo.svg`, `palomar.svg` y sus variantes `-linea.svg`) están en `docs/ilustraciones/` y `docs/ilustraciones/v1/`
> por la misma razón; lo que usa la web está en `public/assets/`.

En la **V2** (comentarios de los novios: «efecto general de acuarela, hecho a mano, con irregularidades a pincel seco») hay
**tres familias**, todas hechas con código, propias y reproducibles (mismas semillas → mismas imágenes):

1. **Rotulado a pincel seco** (§R): títulos de sección, los nombres de la portada, los bordes de las fotos, la aguada de la
   entrada y la pincelada de los botones. `scripts/rotulos/` → `public/assets/rotulos/`.
2. **Acuarelas** (§0): la guirnalda y el bodegón entre la portada y la Agenda, San Pablo y el Palomar (§A) y los iconos
   de Alojamiento y Lista de bodas. `scripts/acuarela/` → `public/assets/ilustraciones/acuarela/`.
3. **A pluma** (§1 en adelante): la ruta con el avión de la Agenda, adornos, iconos y favicon (SVG). San Pablo y el
   Palomar a pluma eran de la V1 y se conservan fuera de la web.


## R. Rotulado a pincel seco (`scripts/rotulos/` → `public/assets/rotulos/`)

- **`alfabeto.py`**: mayúsculas de **un solo trazo**, en el orden y el sentido en que las pinta un rotulista, condensadas
  (avance ≈ 0,62 de la altura) para que los títulos largos quepan en el móvil. Las vocales con tilde, `¡ ! . ·` incluidos.
- **`pincel.py`**: el pincel. Cada trazo se muestrea por longitud de arco; la presión tiene ataque, cuerpo con ruido y
  salida afilada; el pincel son 72 cerdas con su carga, que se van secando con la distancia (flancos más secos,
  deshilachado al final, alguna cerda suelta); el **grano del papel** decide dónde agarra el pigmento, así salen las
  estrías y los bordes rasgados que siguen la dirección del trazo. Cada letra lleva su escala, giro y línea base algo
  distintos, y las curvas cerradas (O, D, B, P, R) se quedan un poco sin cerrar. Solo numpy y Pillow.
- **Tintas** (tras la hoja de muestras, los novios pidieron colores **más claros y suaves, de acuarela**): terracota
  aguada `#ba624c` para títulos y nombres, gris Payne `#68707a` (el negro, aguado) para los acentos (la «y» de los nombres
  y «S.R.C.»), con la tinta transparente (se ven los cruces). Los botones usan `#a84a33`, el `--rojo` de la web.
- **`generar.py`** escribe los WebP y **el marcado en `public/index.html`** entre `<!-- rotulo:ID -->` y
  `<!-- /rotulo:ID -->` (la imagen de cada título con su texto en un `.sr-only`, y el SVG de los nombres con los ejes de
  sus trazos para la animación). Los títulos están en `TITULOS` (texto, semilla, tinta, icono). Comprueba que los ejes de
  los nombres cubren toda la tinta de la imagen.
- **`piezas.py`**: bordes de foto (`borde-sup`, `borde-inf`, `borde-4`, blancos con alfa: se usan como máscaras), la
  aguada de la entrada y la pincelada de los botones.
- **`muestras.py`**: hoja de muestras con variantes de pincel (seco, intermedio, cargado), para elegir.
- Pesos: cada título 11–40 KB (una sola imagen con la mayúscula a 104 px, nítida en móviles 3× y pantallas 2×; el color
  es plano y la textura va en el alfa), nombres ≈ 26 KB, máscaras 3–16 KB.

```bash
python3 scripts/rotulos/generar.py       # ≈ 10 s
python3 scripts/rotulos/muestras.py hoja.png
```


## 0. Acuarelas (`public/assets/ilustraciones/acuarela/*.webp`)

Cada objeto (tomate, vela, copa, girasol, jarra…) se compone de manchas de color con el borde irregular y el pigmento
acumulado en el contorno (filtros SVG que pinta Chromium) y unas líneas de tinta finas. En la V2 la librería (`lib.py`)
pinta más «a mano»: **saturación desigual** dentro de cada mancha, **bordes que a ratos se pierden** en el papel,
**floraciones** (zonas más claras donde el agua empujó el pigmento), grano de papel más visible y **tinta a trazos, fina y
desalineada** con el color (`DESREGISTRO`), como en un boceto de tinta y acuarela. Paleta cálida y apagada (`objetos.PAL`):
terracota, mostaza, verde salvia, rosa polvoriento y crema, más el turquesa del candelabro y el verde botella.

| Fichero | Dónde sale | Tamaños |
|---|---|---|
| `guirnalda-v2-630.webp` | tira de banderines que se repite a todo el ancho, sobre el bodegón | 630 px |
| `bodegon-v2-640/1000.webp` | bodegón de boda rústica: narcisos en un jarrón, vela en candelabro turquesa, copa de rosado, menú, tomates cherry, rodajas de naranja, uvas, girasoles en una jarra de barro, botella verde y tarta | 640 y 1000 px |
| `san-pablo-acuarela-640/960.webp`, `palomar-acuarela-640/960.webp` | Agenda (§A) | 640 y 960 px |
| `almohada-icono-2x/3x.webp`, `alianzas-icono-2x/3x.webp` | iconos a la izquierda de «Alojamiento» y «Lista de bodas», del alto de las mayúsculas | 2× y 3× |

- **Regenerar**: `python3 scripts/acuarela/generar.py` (todas) o `… generar.py bodegon guirnalda` (algunas), y
  `python3 scripts/acuarela/arquitectura.py` (San Pablo y el Palomar). Necesitan Pillow, Node con Playwright y Chromium
  (variables `PLAYWRIGHT_PATH` y `CHROME_PATH` si no están instalados globalmente).
- **Sobre blanco y multiplicadas**: el bodegón, la guirnalda, San Pablo y el Palomar se guardan **sin transparencia**
  (sobre blanco: pesan la tercera parte) y en la página llevan `.acuarela-plana` (`mix-blend-mode: multiply`): el blanco
  desaparece y el color queda transparente sobre el lino, como el pigmento sobre el papel. La animación de aparición
  (`.revelar`) va en la propia imagen, no en un contenedor (si no, mientras este se funde se vería el blanco).
- Los iconos llevan transparencia (son pequeños) y se recortan al dibujo.
- Las escenas de la V1 que ya no salen (ramo con alianzas, almohada grande, maleta, granadas) siguen en `escenas.py`
  (`ESCENAS_V1`) y en la historia del repositorio.
- El fondo de lino con rayas **no** es una acuarela: la textura (`public/assets/img/lino.webp`) sale de
  `scripts/fondo/generar.py` y las rayas rosas son un degradado CSS en `base.css` (`--rosa`, `--p`).


## A. San Pablo y el Palomar en acuarela y a pincel (`scripts/acuarela/arquitectura.py`)

Reutilizan la geometría de los dibujos a pluma de la V1 (`scripts/ilustraciones/san_pablo.py` y `palomar.py`, que no se
tocan): una subclase de `pluma.Lienzo` apunta, mientras se dibujan, los trazos, los polígonos que se iban a rayar y las
aguadas. Con eso se pinta otra cosa: **aguadas de acuarela** (`lib.py`) con la paleta de la V2, **veladuras frías** donde
el dibujo llevaba rayado y un cielo apenas insinuado; y **líneas de pincel** (`scripts/rotulos/pincel.py`): contornos y
detalles con un pincel de tinta, y el rayado y las texturas (sillería, tejas…) con un pincel muy fino y una tinta más
suave. La tinta va un poco desplazada respecto al color.

---

---

## A pluma (resto del documento)

Dibujos a pluma propios (no calcados): la ruta con el avioncito, adornos, iconos y favicon (y San Pablo y el Palomar
de la V1, que ya no se publican: `generar.py` los deja en `docs/ilustraciones/v1/`). Todo es SVG vectorial, transparente, sin `<text>`, sin
imágenes incrustadas, sin `<filter>` y solo con `viewBox` (sin width/height).

- **Regenerar** (determinista, mismas semillas → mismos SVG):
  `python3 scripts/ilustraciones/generar.py` (o `… generar.py san_pablo palomar rutas adornos iconos favicon`).
  Solo usa la biblioteca estándar de Python 3. El motor del trazo está en `scripts/ilustraciones/pluma.py`.
- **Tinta**: `#4b3c37` (marrón grisáceo oscuro, `TINTA` en `pluma.py`) fija en las ilustraciones grandes; rojo `#a84a33` (`ROJO`, el `--rojo` de la V2) en la ruta y el avión (el favicon conserva el `#a3121d` de la V1); `currentColor` en los sprites.
- **Aguadas**: ocre `#c3a063` (piedra/revoco), terracota `#a4563a` (teja, ladrillo, puerta), oliva
  `#6c7550` (árboles, césped), con poca opacidad y desplazadas 2–4 unidades del trazo (desregistro).

| Fichero | viewBox | Peso |
|---|---|---|
| `san-pablo.svg` / `san-pablo-linea.svg` | `0 0 520 620` | 59 / 56 KB |
| `palomar.svg` / `palomar-linea.svg` | `0 0 700 440` | 51 / 48 KB |
| `ruta-vertical.svg` | `0 0 220 560` | 1,3 KB |
| `adornos.svg` (sprite) | por símbolo | 4 KB |
| `iconos.svg` (sprite) | `0 0 48 48` | 5 KB |
| `favicon.svg` | `0 0 64 64` | 0,6 KB |

Recomendación: usar las versiones **con aguada** (`san-pablo.svg`, `palomar.svg`); las `-linea.svg`
son la misma línea sin color, por si se prefiere un acabado solo a tinta.

---

## 1. `san-pablo.svg` y `palomar.svg` (V1, ya no se publican: ver §A)

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

## 2. `ruta-vertical.svg`

> **V2:** los novios pidieron quitar el corazón y que el camino fuera «más serpeante/zigzag para darle volumen»: ahora
> serpentea en cuatro curvas amplias (`rutas.vertical()`, viewBox 220 × 560) y la versión horizontal ya no existe (la
> web usa la misma composición de una columna en todas las pantallas). Lo que sigue describe la V1 y sigue valiendo
> para la estructura (`#ruta` + `#avion`) y el JS del vuelo.

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
