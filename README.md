# Marta y Jorge · invitación de boda

Web de **una sola página** (sin menú, todo en scroll) para la boda del **sábado 8 de mayo de 2027** en Valladolid:

- **12:00** · Ceremonia en la Iglesia de San Pablo
- **14:00** · Celebración en La Posada Real del Pinar (Pozal de Gallinas)

Estilo de papelería de boda: papel de acuarela, caligrafía a pincel, ilustraciones a pluma propias y
formulario de confirmación con acompañantes, autocar y alergias.

## Qué incluye

| Sección | Qué hace |
|---|---|
| **Portada** | Entrada animada (un avión de papel traza la ruta, los nombres se escriben a pluma y unas puertas en arco se abren sobre la foto), cuenta atrás sobria (días · horas · minutos) y botón para confirmar. Guía en [`docs/animacion-entrada.md`](docs/animacion-entrada.md) |
| **Agenda** | Ilustraciones a pluma de San Pablo y del Palomar unidas por una ruta con un lazo en forma de corazón y un avión que la recorre; botones «¿Cómo llegar?» a Google Maps y enlace «Añadir al calendario» |
| **Transporte** | Coche (parking recomendado junto a la Catedral) y autocar |
| **Alojamiento** | Texto y mapa con la zona recomendada marcada con un círculo «a rotulador» |
| **S.R.C.** | Formulario: nombre, asistencia, acompañantes con sus nombres, plazas de autocar por trayecto, alergias por persona y mensaje. No pide correo |
| **Lista de bodas** | IBAN con botón para copiarlo |
| **Cierre** | «¡Os esperamos!» sobre la foto del atardecer |
| **`/admin`** | Panel privado (con contraseña) para que los novios vean totales, filtren y descarguen CSV |

Stack: HTML/CSS/JS **sin build ni frameworks** · hosting y funciones en **Vercel** · datos en **Supabase** (Postgres).

## Estructura

```
public/                 ← lo que se publica
  index.html            la página entera
  boda-marta-y-jorge.ics   «Añadir al calendario» (ceremonia y celebración)
  css/                  base.css (diseño: colores, fuentes) · site.css (secciones) · intro.css (entrada de la portada) · rsvp.css · mapa.css
  js/                   boot.js · main.js (animaciones, cuenta atrás, copiar IBAN) · intro.js (saltar la entrada, parallax) · rsvp.js · mapa.js
  assets/fonts/         tipografías autoalojadas y recortadas (Ephesis, Cormorant cursiva, Inter 400/500: ~60 KB)
  assets/img/           fotos optimizadas (WebP), textura de papel, imagen para compartir (og.jpg)
  assets/ilustraciones/ SVG a pluma: San Pablo, Palomar, ruta, adornos, iconos, favicon (guía: docs/ilustraciones.md)
  admin/                panel de respuestas
api/                    funciones serverless de Vercel (rsvp, admin, ping)
supabase/               schema.sql (tabla y vistas) · consultas.sql (consultas listas para pegar)
scripts/                dev.mjs (servidor local) · test-rsvp.mjs · ilustraciones/ (generador de los SVG) · intro/ (generador de los nombres a pluma) · og/ (imagen para compartir el enlace)
docs/                   rsvp.md (guía completa del formulario y los datos) · animacion-entrada.md · ilustraciones.md · contenido-original.md (brief)
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

> **Estado actual** · El WhatsApp de contacto ya está puesto (`data-whatsapp` en `public/index.html`). Pendiente:
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
| Teléfono (WhatsApp) o correo de contacto | atributos `data-whatsapp` / `data-email` de `<section id="alojamiento">`: aparece el botón de contacto y, si falla un envío, el formulario ofrece mandar la respuesta por ahí |
| IBAN | `public/index.html`, sección *Lista de bodas* (texto visible y atributo `data-copiar`). Se ve siempre en una sola línea: el tamaño de la letra se adapta al ancho disponible (`.iban__numero` en `site.css`) |
| Colores y tipografías | variables de `:root` en `public/css/base.css`. Los fondos claros de campos, opciones, tarjeta e IBAN son translúcidos (`--campo`, `--campo-activo`, `--campo-mapa`) para que se vea la textura del papel; subid o bajad su opacidad ahí |
| Fotos | `public/assets/img/` (WebP; la de la portada es un recorte 4:5) |
| Ilustraciones | `public/assets/ilustraciones/` (guía en [`docs/ilustraciones.md`](docs/ilustraciones.md)); se regeneran con `python3 scripts/ilustraciones/generar.py` |
| Mensajes del formulario | arriba de `public/js/rsvp.js` y atributos `data-texto-si` / `data-texto-no` en `index.html` |
| Horas del «Añadir al calendario» | `public/boda-marta-y-jorge.ics` (texto plano; las horas están en UTC: 12:00 de Madrid en mayo = `10:00Z`. La ceremonia dura 1 h y la celebración está marcada hasta las 23:00: cambiad `DTEND` si queréis otra hora) |
| Tamaño de la portada según la pantalla | variables `--n` (nombres) y `--foto` en el bloque `.portada` de `public/css/site.css` |
| Entrada de la portada | tiempos en `public/css/intro.css`; ver [`docs/animacion-entrada.md`](docs/animacion-entrada.md). Se reproduce en cada carga (se acelera con un toque o un scroll); `?intro=0` en la dirección la omite |

## Rendimiento y pantallas

- **Carga ligera**: la primera visita descarga ≈ 190–210 KB en un móvil (comprimido; antes ≈ 360 KB) y ≈ 380–450 KB
  si se recorre la página entera (antes ≈ 550–650 KB). Las fotos van en WebP con varios tamaños (el navegador
  elige el que necesita su pantalla) y las ilustraciones, el mapa y la foto del cierre se piden solo al
  acercarse. Las fuentes están recortadas al español: de ≈ 190 KB a ≈ 60 KB.
  Si añadís fuentes o fotos, comprimidlas igual (WebP, anchos de 480/600/840 px) para no perder esto.
- **Pantallas**: la portada se dimensiona con el ancho **y el alto** de la pantalla. En el móvil en vertical ocupa
  exactamente la pantalla (nombres, fecha, foto, cuenta atrás y botón se ven sin hacer scroll, de 320×548 a tablets) y
  también entra entera en móviles apaisados, portátiles bajos y monitores grandes (probada de 240 a 3440 px de ancho).
  Con la letra del sistema ampliada no se sale nada de la pantalla en ≥ 320 px de ancho.
- **Entrada animada**: se reproduce en cada carga y se puede saltar con un toque o un scroll; ver [`docs/animacion-entrada.md`](docs/animacion-entrada.md).

## Notas de diseño

- Las tres webs de referencia que enviasteis estaban bloqueadas en el entorno donde se construyó esto, así que el estilo
  se dedujo de vuestra descripción y de las capturas del Word. Todo el aspecto sale de variables en `base.css`:
  ajustarlo a una referencia concreta es cuestión de minutos.
- Las ilustraciones de **San Pablo** y del **Palomar** son dibujos propios hechos a pluma (no calcados de la acuarela
  ni del render con IA). Si contratáis al ilustrador para las invitaciones en papel, basta con sustituir `san-pablo.svg`
  por su versión (mismo `viewBox`) o dejar esta.
- La página lleva `noindex` y `robots.txt` cerrado: es una invitación privada y no debe salir en buscadores.
- Todo está autoalojado (fuentes, imágenes, scripts): solo se piden a terceros las teselas del mapa.
