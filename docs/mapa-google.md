# Mapa de alojamiento con Google Maps

El mapa de la sección Alojamiento (`public/js/mapa.js` + `public/css/mapa.css`) usa la **Maps JavaScript API**
con un mapa vectorial y un **Map ID**. Se carga solo cuando el visitante llega a esa sección.

## Dónde van la clave y el Map ID

En `public/index.html`, en el contenedor del mapa:

```html
<div id="mapa-alojamiento" class="mapa marco" data-api-key="AIza…" data-map-id="ee2adbb68a2af545c55430ab" …>
```

- `data-map-id`: el Map ID «martayjorge-web» (JavaScript, Vector). Ya está puesto.
- `data-api-key`: la clave de Google Maps (ya puesta). **Si se deja vacío, el mapa muestra «No hemos podido cargar el mapa»**
  con el enlace a Google Maps (la leyenda se ve igual).

La clave de Maps JavaScript siempre acaba en el navegador del visitante: no es un secreto y puede ir en el HTML.
Lo que la protege es restringirla en Google Cloud (abajo). **No** la pongas en las variables de entorno de Vercel:
la web es estática y no las leería.

## Restringir la clave (Google Cloud → APIs y servicios → Credenciales)

1. **Restricciones de aplicación → Sitios web** (HTTP referrers). No sirve «Direcciones IP»: esa opción es para
   servidores, y con ella el mapa del navegador falla. Añade:
   - `https://martayjorge-eta.vercel.app/*` (y el dominio definitivo cuando lo haya, p. ej. `https://www.tudominio.com/*`)
   - `https://*.vercel.app/*` si queréis probar en las vistas previas de Vercel
   - `http://localhost:*/*` y `http://127.0.0.1:*/*` para `npm run dev`
2. **Restricciones de API**: solo «Maps JavaScript API».
3. **Cuotas** (APIs y servicios → Maps JavaScript API → Cuotas): un tope diario de cargas (p. ej. 1.000) evita
   cualquier susto en la factura.

## Colores del mapa (estilo del Map ID)

Los colores de calles, río, parques y qué etiquetas se ven **no están en el código**: se cambian en
Google Cloud → Google Maps Platform → **Estilos de mapa**, en el estilo asociado al Map ID. Al guardar y publicar
el estilo, la web lo coge sola (puede tardar unos minutos). Valores que encajan con la web y con el plano de referencia:

| Elemento | Color | Notas |
|---|---|---|
| Suelo, manzanas | `#ece6dc` | beige |
| Edificios | `#e2dacd` | un poco más oscuro que el suelo |
| Calles | `#ffffff` | borde `#e6ded2` |
| Agua (río Pisuerga) | `#a9d3e0` | |
| Parques (Campo Grande) | `#cfe5c0` | |
| Puntos de interés (comercios, restaurantes…) | ocultos | para que solo se vean los marcadores de la boda |
| Transporte público | oculto | |
| Etiquetas de calles | solo las principales | o todas en gris claro `#9a8f84` |

## Qué dibuja la web encima del mapa

Todo está en `CFG` al principio de `js/mapa.js`:

- `zonas.recomendada` y `zonas.comoda`: los dos óvalos (centro, semiejes en metros y giro en grados).
- `rotulos`: «Zona recomendada» y «¡la más cómoda!».
- `puntos`: San Pablo y Plaza del Poniente (tarjeta con detalle), Plaza Mayor y Catedral (icono y nombre),
  Plaza de Zorrilla (punto) y Campo Grande (rótulo). Los que llevan `destino` abren «¿Cómo llegar?».

La leyenda («Dónde alojarse») es HTML normal en `index.html`: en pantallas anchas va encima del mapa, abajo a la
derecha; en el móvil, debajo.

## Seguridad (CSP) en `vercel.json`

La cabecera `Content-Security-Policy` permite los dominios de Google que necesita la API
(`*.googleapis.com`, `*.gstatic.com`, `*.google.com`, `fonts.gstatic.com`), `blob:` para los workers del mapa
vectorial y `'unsafe-eval'`, que Google incluye en su guía de CSP para la API
(https://developers.google.com/maps/documentation/javascript/content-security-policy).
`npm run dev` aplica las mismas cabeceras, así que un fallo de CSP se ve ya en local (consola del navegador).

## Si algo falla

Abre la consola del navegador (F12):

- `RefererNotAllowedMapError`: falta el dominio en «Sitios web» de la clave.
- `InvalidKeyMapError` / `ApiNotActivatedMapError`: clave mal copiada o API sin activar.
- `Refused to load… Content Security Policy`: falta un dominio en la CSP de `vercel.json`.
- El mapa sale gris o sin estilo: el Map ID no tiene un estilo asociado o no está publicado.
