# Marta y Jorge · invitación de boda

Web de **una sola página** (sin menú, todo en scroll) para la boda del **sábado 8 de mayo de 2027** en Valladolid:

- **12:00** · Ceremonia en la Iglesia de San Pablo
- **14:00** · Celebración en La Posada Real del Pinar (Pozal de Gallinas)

Estilo de papelería de boda pintada a mano: **lino crema con rayas rosas**, **rotulado a pincel de acuarela en rojo** (con
subrayados a mano, como la invitación de referencia que mandaron los novios), cursiva con serifas, **acuarelas propias** y
fotos de lado a lado con los bordes a pincel; formulario de confirmación con acompañantes, autocar y alergias.

> **Versiones** · En producción conviven tres versiones con un **selector «V1 · V2 · V3»** fijo arriba a la derecha:
> - **V3** (la más nueva: la V2 con los cambios de los novios del 28-oct-2026) vive en `public/v3/index.html`, en
>   `/v3/`. Usa rutas absolutas y comparte estilos, scripts e imágenes con la V2; lo suyo está en `public/css/v3.css`
>   y en los ficheros `*-v3`. Cambios: bodegón sin la guirnalda de banderines, ruta San Pablo → Posada un 30 % más
>   corta (`ruta-vertical-v3.svg`), alianzas con el diamante por fuera del aro (`alianzas-icono-v3-*.webp`) y, en
>   Alojamiento, un **plano ilustrado fijo** en lugar de Google Maps (sin API ni clave; ver «Plano de la V3» abajo).
> - **V2** es la página de siempre, `public/index.html`, en `/` (con el mapa de Google Maps).
> - **V1** (la primera, congelada en el commit `db679a3`, con el mapa de Google Maps) vive en `public/v1/`, en `/v1/`.
>   Lleva `<base href="/v1/">` para cargar sus propios estilos, scripts e imágenes.
> - Quien llega a `/` sin haber elegido ve la **V1**; al pulsar otra versión se queda en ella y se recuerda en el
>   navegador. Enlaces directos: `/v1/?v=1`, `/?v=2` y `/v3/?v=3`. Lo hacen `public/version/elegir.js` (en el
>   `<head>` de la V2) y `public/version/selector.js` + `selector.css` (en las tres).
> - Las tres versiones envían las confirmaciones a la misma API (`/api/rsvp`).
> - **Para quedarse con una sola**: borrar las carpetas de las otras y `public/version/`, y quitar de la página que
>   quede las líneas que cargan `/version/…`. Si se queda la V3, lo más limpio es moverla a `public/index.html`.
>   **Para que por defecto se vea la V2** (sin quitar el selector): borrar solo la línea de `elegir.js`.

## Qué incluye

| Sección | Qué hace |
|---|---|
| **Portada** | Entrada animada (los nombres se pintan a pincel de acuarela trazo a trazo, la fecha también va rotulada y la foto, de lado a lado con los bordes a pincel, aparece con una aguada), cuenta atrás sobria (días · horas · minutos) y botón para confirmar. Cabe entera en una pantalla. Guía en [`docs/animacion-entrada.md`](docs/animacion-entrada.md) |
| **Mesa puesta** | Bodegón de acuarela (narcisos, vela en candelabro turquesa, copa de rosado, menú, tomates cherry, naranjas, uvas, girasoles, botella y tarta) bajo una guirnalda, entre la portada y la Agenda |
| **Agenda** | San Pablo y el Palomar en acuarela y a pincel, unidos por un caminito rojo que serpentea y un avión que lo recorre; enlaces «¿Cómo llegar?» a Google Maps y «Añadir al calendario» |
| **Transporte** | Coche (parking recomendado junto a la Catedral) y autocar |
| **Alojamiento** | Texto y mapa de Google Maps con la zona recomendada (de la Plaza del Poniente a San Pablo) y la más cómoda (junto a Poniente), tarjetas de los lugares y leyenda. Icono de acuarela (almohada y llave) junto al título. Configuración: `docs/mapa-google.md` |
| **Foto de la playa** | De lado a lado, aparece con una aguada |
| **S.R.C.** | «S.R.C. · Se ruega confirmación» y el formulario: nombre, asistencia, acompañantes con sus nombres, plazas de autocar por trayecto, alergias por persona y mensaje. No pide correo |
| **Lista de bodas** | Dos alianzas en acuarela junto al título e IBAN en una sola línea con botón para copiarlo |
| **Cierre** | «¡Os esperamos!» sobre el cielo de la foto del atardecer, que se ve entera. Es el final de la página |
| **`/admin`** | Panel privado (con contraseña) para que los novios vean totales, filtren y descarguen CSV |

Todos los títulos son rótulos pintados con el motor de pincel de `scripts/rotulos/` (el texto va en un `.sr-only`
para lectores de pantalla). Una sola composición, la del móvil, en todas las pantallas (en escritorio, centrada).

Stack: HTML/CSS/JS **sin build ni frameworks** · hosting y funciones en **Vercel** · datos en **Supabase** (Postgres).

## Estructura

```
public/                 ← lo que se publica
  index.html            la página entera (V2)
  v1/                   la V1 congelada (commit db679a3), para compararla con el selector · version/ (el selector)
  boda-marta-y-jorge.ics   «Añadir al calendario» (ceremonia y celebración)
  css/                  base.css (diseño: colores, fuentes) · site.css (secciones) · intro.css (entrada de la portada) · rsvp.css · mapa.css
  js/                   boot.js · main.js (animaciones, cuenta atrás, copiar IBAN) · intro.js (saltar la entrada, parallax) · rsvp.js · mapa.js
  assets/fonts/         tipografías autoalojadas y recortadas (Covered By Your Grace, Playfair Display cursiva, Inter 400/500: ~58 KB)
  assets/img/           fotos optimizadas (WebP), textura de lino (lino.webp), imagen para compartir (og.jpg) e icono del móvil
  assets/rotulos/       rótulos a pincel de acuarela (títulos, nombres y fecha), máscaras de los bordes de las fotos, aguada y pincelada de botón
  assets/ilustraciones/ acuarela/ (bodegón, San Pablo, Palomar, iconos…) y SVG a pluma (ruta, adornos, iconos, favicon); guía: docs/ilustraciones.md
  admin/                panel de respuestas
api/                    funciones serverless de Vercel (rsvp, admin, ping)
supabase/               schema.sql (tabla y vistas) · consultas.sql (consultas listas para pegar)
scripts/                dev.mjs (servidor local) · test-rsvp.mjs · rotulos/ (pincel: rótulos, nombres, fecha, bordes de foto) · acuarela/ (acuarelas, San Pablo y Palomar) · ilustraciones/ (SVG a pluma) · fondo/ (textura de lino) · og/ (imagen para compartir el enlace y el icono del móvil)
docs/                   rsvp.md (guía completa del formulario y los datos) · animacion-entrada.md · ilustraciones.md · contenido-original.md (brief) · datos-verificados.md · ilustraciones/v1/ (dibujos a pluma de la V1)
vercel.json             salida en public/, cabeceras de seguridad, cron diario
```

## Probarla en local

Requisitos: Node 18 o superior. No hay dependencias que instalar.

```bash
npm run dev     # http://127.0.0.1:3000 · la web + la API con un Supabase SIMULADO (no toca nada real)
npm test        # pruebas de la API
```

Los envíos de prueba se guardan en `.dev-data/rsvps.json` (ignorado por git). El panel en local:
`http://127.0.0.1:3000/admin` (contraseña `desarrollo-local-2027`). Más detalles en [`docs/rsvp.md`](docs/rsvp.md).

## Publicarla (GitHub + Vercel + Supabase + dominio)

> **Estado actual** · El WhatsApp de contacto ya está puesto (`data-whatsapp` en la sección `#confirmacion` de
> `public/index.html`: lo usa el formulario si falla un envío). Pendiente:
> conectar **Supabase** (hasta entonces, si alguien pulsa «Enviar confirmación», la web le ofrece mandar la respuesta
> por WhatsApp, ya escrita, y no se guarda nada) y elegir el **dominio** definitivo (mientras tanto sirve el
> `martayjorge-eta.vercel.app` que da Vercel; las metaetiquetas `og:` de `index.html` llevan ese mismo dominio temporal).

1. **GitHub**: el código ya está en este repositorio, en la rama `main`. Conviene que sea también la rama principal
   (*Settings → Branches → Default branch*).
   El repositorio es **público**: cualquiera puede ver en GitHub lo que hay en `public/` (el IBAN y el teléfono).
   Si preferís que no sea así, ponedlo privado (*Settings → General → Change visibility*); Vercel lo importa igual.
2. **Supabase** (guía paso a paso en [`docs/rsvp.md`](docs/rsvp.md) §3):
   crear un proyecto nuevo (por ejemplo `martayjorge`, región europea), abrir **SQL Editor**, pegar todo
   [`supabase/schema.sql`](supabase/schema.sql) y ejecutarlo. Copiar la **URL del proyecto** y la
   **clave secreta** (`sb_secret_…`; las claves antiguas `service_role` dejan de funcionar a finales de 2026).
3. **Vercel**: *Add New → Project* → importar este repositorio. Framework: **Other**; no hace falta comando de
   build (`vercel.json` ya indica que se publica `public/`). Añadir en *Settings → Environment Variables*:

   | Variable | Valor |
   |---|---|
   | `SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `SUPABASE_SECRET_KEY` | `sb_secret_…` (marcarla como *Sensitive*) |
   | `ADMIN_TOKEN` | contraseña del panel `/admin` (mínimo 12 caracteres) |
   | `CRON_SECRET` | texto largo y aleatorio (protege `/api/ping`) |

   Después, *Redeploy* (las variables solo se aplican a despliegues nuevos). La **rama de producción** debe ser
   `main` (*Settings → Git → Production Branch*).
4. **Dominio**: *Settings → Domains* → añadir el dominio elegido (p. ej. `martayjorge.com`) y crear en el
   registrador los registros DNS que indique Vercel. Después, sustituir `https://martayjorge-eta.vercel.app` por el
   dominio definitivo en las 3 metaetiquetas de `public/index.html` (`og:url`, `og:image`, `twitter:image`); si no,
   la vista previa al compartir el enlace por WhatsApp seguirá apuntando al dominio temporal.
5. **Probar antes de repartir la invitación**: abrir la web, enviar una confirmación como «Prueba Marta»,
   comprobarla en `/admin`, borrar las pruebas (`docs/rsvp.md` §5) y compartir el enlace en un chat para ver la
   vista previa.

> **Plan gratuito de Supabase**: pausa los proyectos con poca actividad durante 7 días y un proyecto pausado no
> guarda confirmaciones. Por eso `vercel.json` incluye un cron diario (`/api/ping`) que lo mantiene despierto.
> Aun así, conviene vigilar los correos de Supabase durante los meses de confirmaciones.

## ¿Dónde se guardan las respuestas y cómo accedo?

En la tabla `rsvps` de **vuestro proyecto de Supabase**. Tres formas de verlas (de más fácil a más completa):

1. **`https://vuestro-dominio/admin`** + la contraseña `ADMIN_TOKEN`: totales, filtros, lista por persona y botones
   de **descargar CSV** (abre bien en Excel).
2. **Supabase → Table Editor**: tablas `rsvps` (todo lo recibido), `rsvp_vigentes` (última respuesta de cada
   persona), `rsvp_personas` (una fila por invitado/acompañante, con alergias) y `rsvp_resumen` (totales).
3. **Supabase → SQL Editor** con las consultas de [`supabase/consultas.sql`](supabase/consultas.sql).

No se guardan correos ni direcciones IP. Los datos de alergias son sensibles: usadlos solo para organizar la
boda y, después, exportad lo que queráis conservar y vaciad la tabla. Guía completa: [`docs/rsvp.md`](docs/rsvp.md).

## Cómo cambiar cosas

| Quiero cambiar… | Dónde |
|---|---|
| Fecha u hora de la cuenta atrás | `data-cuenta` en `public/index.html` (hora de Madrid, formato `2027-05-08T12:00:00+02:00`) |
| Quitar la cuenta atrás | borrar el bloque `<div class="cuenta" …>` de la portada |
| Textos, horarios, enlaces «¿Cómo llegar?» | `public/index.html` |
| Teléfono (WhatsApp) o correo de contacto | atributos `data-whatsapp` / `data-email` de `<section id="confirmacion">`: si falla un envío, el formulario ofrece mandar la respuesta por ahí (en la V2 ya no hay botón de contacto visible) |
| IBAN | `public/index.html`, sección *Lista de bodas* (texto visible y atributo `data-copiar`). Se ve siempre en una sola línea: el tamaño de la letra se adapta al ancho disponible (`.iban__numero` en `site.css`) |
| Colores y tipografías | variables de `:root` en `public/css/base.css` (`--rojo`, rojo acuarela `#b23a40`, es la tinta de botones, fechas y subrayados; `--rosa` y `--p` las rayas del fondo). Los fondos claros de tarjeta, opciones, botones e IBAN son translúcidos (`--campo`, `--campo-activo`, `--campo-mapa`) para que se vea el lino |
| Títulos, nombres, bordes de las fotos, pincelada de los botones | `scripts/rotulos/` (textos, semillas y tintas en `generar.py`); `python3 scripts/rotulos/generar.py` rehace las imágenes y el marcado en `index.html`. Guía en [`docs/ilustraciones.md`](docs/ilustraciones.md) §R |
| Fondo (lino y rayas) | la textura sale de `python3 scripts/fondo/generar.py` (`public/assets/img/lino.webp`); las rayas son un degradado CSS en el `body` de `base.css` (ancho de cada pareja: `--p`; color e intensidad: `--rosa` y `--rosa-hueco`, cuanto menor es el último número, más suaves se ven) |
| Ilustraciones de acuarela | `scripts/acuarela/` (objetos y escenas; se regeneran con `python3 scripts/acuarela/generar.py`; San Pablo y el Palomar, con `arquitectura.py`); la guía está en [`docs/ilustraciones.md`](docs/ilustraciones.md) |
| Fotos | `public/assets/img/` (WebP; la de la portada es un recorte 4:5). Si cambian los nombres o la foto, `node scripts/og/generar.cjs` rehace la imagen para compartir y el icono |
| Ruta de la Agenda, iconos y adornos (SVG a pluma) | `public/assets/ilustraciones/` (guía en [`docs/ilustraciones.md`](docs/ilustraciones.md)); se regeneran con `python3 scripts/ilustraciones/generar.py` |
| Mensajes del formulario | arriba de `public/js/rsvp.js` y atributos `data-texto-si` / `data-texto-no` en `index.html` |
| Horas del «Añadir al calendario» | `public/boda-marta-y-jorge.ics` (texto plano; las horas están en UTC: 12:00 de Madrid en mayo = `10:00Z`. La ceremonia dura 1 h y la celebración está marcada hasta las 23:00: cambiad `DTEND` si queréis otra hora) |
| Tamaño de la portada según la pantalla | variables `--n` (ancho de los nombres) y `--foto-h` (alto de la foto) en el bloque `.portada` de `public/css/site.css` |
| Zona recomendada del mapa (óvalo) | `CFG.centro` y `CFG.semiejes` en `public/js/mapa.js` (medidas y criterios en [`docs/datos-verificados.md`](docs/datos-verificados.md) §6) |
| Entrada de la portada | tiempos en `public/css/intro.css`; ver [`docs/animacion-entrada.md`](docs/animacion-entrada.md). Se reproduce en cada carga (se acelera con un toque o un scroll); `?intro=0` en la dirección la omite |

## Rendimiento y pantallas

- **Peso** (medido en un móvil 3× de 390 px, con HTML/CSS/JS comprimidos como los sirve Vercel): la portada y lo que se
  pide en los primeros segundos ≈ 390 KB; la página entera ≈ 820 KB (la V1, medida igual: ≈ 310 y ≈ 640 KB). La
  diferencia son las acuarelas en imagen (San Pablo, el Palomar) y los rótulos a pincel. Las fotos van en WebP con varios
  tamaños (el navegador elige el que necesita su pantalla), las acuarelas grandes van sobre blanco y se multiplican con el
  lino (pesan la tercera parte que con transparencia) y todo lo que está por debajo de la portada se pide al acercarse.
  Las fuentes están recortadas al español (≈ 57 KB). Si añadís fotos, comprimidlas igual (WebP, anchos de 480/600/840 px).
- **Pantallas**: la portada se dimensiona con el ancho **y el alto** de la pantalla. En el móvil en vertical ocupa
  exactamente la pantalla (nombres, fecha, foto de lado a lado, cuenta atrás y botón se ven sin hacer scroll) y también
  entra entera en móviles apaisados, tablets y monitores (comprobada de 320×568 a 1440×900). La página entera mide en un
  móvil de 390 px ≈ 5.700 px de alto (la V1, ≈ 8.200).
  Con la letra del sistema ampliada no se sale nada de la pantalla en ≥ 320 px de ancho.
- **Entrada animada**: se reproduce en cada carga y se puede saltar con un toque o un scroll; ver [`docs/animacion-entrada.md`](docs/animacion-entrada.md).

## Notas de diseño

- **Estilo**: se tomó como referencia el de las capturas de una web de boda de Kurama Estudio que enviasteis (lino crema con
  rayas rosas, rotulado a mano rojo en mayúsculas, cursiva roja para los lugares, campos de formulario subrayados). Se ha
  recreado el *estilo*, no sus dibujos: **las ilustraciones son propias** y las letras son tipografías libres parecidas
  (Covered By Your Grace y Playfair Display, licencia OFL; las licencias están junto a las fuentes). Si queréis exactamente
  las ilustraciones de esa web, hay que encargárselas o comprarlas a su autora. Todo el aspecto sale de variables en `base.css`.
- **V2** (comentarios de los novios): efecto general de acuarela hecha a mano. Los títulos, los nombres y la fecha son
  **rótulos pintados con un pincel de acuarela simulado** (`scripts/rotulos/`), en rojo acuarela y con subrayados a mano,
  en el estilo de la invitación de referencia pero más legibles (lo eligieron con dos hojas de muestras); no es una
  tipografía, así que cada letra es algo distinta.
- Las ilustraciones de **San Pablo** y del **Palomar** son dibujos propios (no calcados de la acuarela ni del render con
  IA): en la V1 a pluma; en la V2, la misma geometría pintada en acuarela y a pincel (`scripts/acuarela/arquitectura.py`).
  Si contratáis al ilustrador para las invitaciones en papel, basta con sustituir `san-pablo-acuarela-*.webp` por su
  versión (sobre blanco, se multiplica con el lino) o dejar esta.
- La página lleva `noindex` y `robots.txt` cerrado: es una invitación privada y no debe salir en buscadores.
- Todo está autoalojado (fuentes, imágenes, scripts): solo el mapa se pide a terceros (Google Maps, con su clave y Map ID en `index.html`; ver `docs/mapa-google.md`).

## Plano de la V3

El mapa de Alojamiento de la V3 es una imagen fija (`public/assets/mapa/valladolid-v3.svg`) dibujada con datos de
OpenStreetMap por `scripts/mapa/generar.py`: calles, río y parques reales, y el óvalo entre la Plaza del Poniente y
San Pablo. No necesita API, clave ni conexión con Google. Los iconos (`san-pablo.svg`, `autocar.svg`) y los rótulos
van en HTML encima (`v3/index.html`), colocados en % del plano. Para cambiar el óvalo o el encuadre, toca las
constantes del script y vuelve a ejecutarlo (`python3 scripts/mapa/generar.py`); imprime las posiciones nuevas.
La atribución «© colaboradores de OpenStreetMap» es obligatoria (licencia ODbL) y va bajo el plano.
