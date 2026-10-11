# Animación de entrada de la portada

Está pensada como una invitación pintada a mano: **lino, acuarela y pincel seco**. Nada de destellos ni rebotes;
todo es suave y se puede saltar en cualquier momento.

## Qué se ve (≈ 4,5 s)

| t (s) | Qué pasa |
|---|---|
| 0,75 | «¡Nos casamos!» aparece con un fundido suave |
| 0,85 – 3,25 | **«MARTA Y JORGE» se pintan a pincel seco**, trazo a trazo y en el orden en que los pinta un rotulista (la M en cuatro golpes, la O de una vuelta que no llega a cerrar…). La «y» va en gris Payne; el resto, en terracota |
| 2,1 – 3,7 | La foto aparece con una **aguada**: un frente de agua con el borde rasgado la «pinta» de arriba abajo |
| 3,0 – 4,35 | La fecha, la cuenta atrás y el botón entran con un fundido |

La foto va de lado a lado en el móvil, con los bordes de arriba y abajo deshechos en pinceladas; en pantallas anchas va
en una caja 4:5 con los cuatro bordes a pincel.

## Cómo está hecha

- **CSS**: [`public/css/intro.css`](../public/css/intro.css). Todas las animaciones son de tipo «desde»: el estado
  normal de cada elemento es el **final**. Por eso, sin animaciones la portada sale completa al instante.
- **Los nombres** son una imagen pintada con el motor de pincel (`public/assets/rotulos/nombres.webp`) dentro de un
  SVG. Una máscara con los **ejes de cada trazo** (los mismos con los que se pintó la imagen) se dibuja con
  `stroke-dashoffset` y va descubriendo la imagen; al acabar (`--fin`, lo escribe el generador en el SVG) se funde con la
  imagen entera, sin máscara. Si algún navegador no animara la máscara, los nombres aparecen igual en ese fundido.
- **La aguada** es una máscara (`public/assets/rotulos/aguada.webp`: un tercio opaco, un frente rasgado y un tercio
  transparente, a 100 % × 300 %) que se desplaza con `mask-position`. Al terminar la entrada se quita la máscara.
- **Espera a los nombres**: la entrada no arranca hasta tener decodificada la imagen de los nombres (26 KB; no se
  precarga con `<link rel="preload">` porque el `<image>` del SVG no reaprovecha esa descarga y se bajaría dos veces);
  como mucho espera 2,5 s ([`public/js/boot.js`](../public/js/boot.js) y
  [`public/js/intro.js`](../public/js/intro.js)).
- **Conexión lenta**: si a los 1,9 s la foto aún no ha llegado, la aguada espera a que llegue (como mucho 9 s).
- **Se salta**: si la persona hace scroll, toca o pulsa una tecla durante la entrada, todo se acelera ×7.
- **Se reproduce siempre**, en cada carga de la página. `?intro=0` en la dirección la omite, y tampoco se reproduce si
  el enlace lleva un ancla (por ejemplo `https://tu-dominio/#confirmacion`).
- **Accesibilidad**: con «reducir movimiento» activado en el sistema no hay animación (portada completa al instante).
  Los nombres siguen siendo texto para lectores de pantalla (`<h1>` con «Marta y Jorge»; el SVG va oculto para ellos).
- **Sin JavaScript** la entrada también se reproduce (es CSS); solo se pierde el avance rápido.

## Retocarla

| Quiero… | Dónde |
|---|---|
| Que empiece antes/después una fase | variables `--escritura` (nombres) y `--abre` (aguada de la foto) al principio de `intro.css` (si cambia `--abre`, ajustad también `DURACION_MS` y los 1900 ms de la espera de la foto en `intro.js`) |
| Que fecha/cuenta atrás/botón entren antes o después | `style="--d:…"` de esos elementos en `public/index.html` |
| Pintar los nombres más rápido o despacio | en `scripts/rotulos/generar.py`, función `nombres()`: `escala = 2.4 / total` (2,4 s en total) y regenerar |
| Cambiar los nombres, el pincel o las tintas | `scripts/rotulos/` (ver [`ilustraciones.md`](ilustraciones.md) §R) y `python3 scripts/rotulos/generar.py`, que reescribe el SVG de `index.html` |
| Desactivar toda la entrada | añadir la clase `intro-vista` a `<html>` en `index.html` (o quitar el `<link>` a `intro.css`) |

## Probarla fotograma a fotograma

En la consola del navegador (recién cargada la página), para congelar la animación en el segundo 2,6:

```js
document.getAnimations().forEach(a => { a.pause(); a.currentTime = 2600; });
```

La entrada de la V1 (avión con el lazo en forma de corazón, nombres a pluma y puertas en arco) está en la etiqueta git
`v1` y en la historia del repositorio.
