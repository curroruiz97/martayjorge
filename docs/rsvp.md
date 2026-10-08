# Confirmación de asistencia (RSVP)

> **En 30 segundos, para Marta y Jorge**
>
> - Cada confirmación se guarda en **vuestra base de datos de Supabase**, en la tabla `rsvps`.
> - Para verlas, lo más fácil: abrid **`https://vuestro-dominio/admin`**, escribid vuestra contraseña
>   y tendréis los totales, la lista de respuestas y un botón **«Descargar CSV»** (se abre en Excel).
> - También podéis verlas en **supabase.com → vuestro proyecto → Table Editor**.
> - Nadie más puede leerlas: la web nunca deja ver la base de datos y la clave solo vive en Vercel.

---

## 1. ¿Dónde se guardan los datos? ¿Cómo puedo acceder?

*(Es la pregunta del documento original: «Los datos del formulario dónde se guardan? Cómo puedo acceder?»)*

Se guardan en **Supabase**, un servicio de base de datos (Postgres) en la nube, en vuestro propio
proyecto. Hay tres formas de consultarlos, de más fácil a más completa:

### Opción A · El panel `/admin` (recomendada)

1. Entrad en `https://vuestro-dominio/admin` (desde el móvil también funciona).
2. Escribid la contraseña: es el valor que pusisteis en Vercel como `ADMIN_TOKEN`.
3. Veréis:
   - **Totales**: personas que asisten (acompañantes incluidos), respuestas «sí», quién no puede
     venir y plazas de autocar de ida y de vuelta.
   - **Alergias e intolerancias**: cuántas personas tienen cada una.
   - **Respuestas**: una tarjeta por persona, con buscador y filtros (todas / asisten / no asisten).
4. Botones **«Descargar CSV»** (una fila por respuesta) y **«CSV por persona»** (una fila por cada
   invitado y acompañante con sus alergias: perfecto para el catering y las mesas).

La contraseña solo se recuerda en esa pestaña del navegador; al cerrarla o pulsar «Salir» hay que
volver a escribirla.

### Opción B · Supabase → Table Editor

1. Entrad en [supabase.com](https://supabase.com) → vuestro proyecto → **Table Editor** (menú izquierdo).
2. Elegid qué ver:
   - `rsvps`: **todas** las respuestas tal cual llegaron (si alguien modificó su respuesta, están las dos).
   - `rsvp_vigentes`: la **última respuesta de cada persona** (la que cuenta).
   - `rsvp_personas`: **una fila por persona que asiste** (invitado + acompañantes) con sus alergias.
   - `rsvp_resumen`: los **totales** en una sola fila.
3. Para descargar: la opción de **exportar a CSV** del Table Editor (según la versión del panel está
   en el botón **Export** o en el menú **⋯** de la tabla). Si no la encontráis, usad la opción C.

### Opción C · Supabase → SQL Editor (consultas preparadas)

En [`supabase/consultas.sql`](../supabase/consultas.sql) hay consultas listas para copiar y pegar:
resumen, quién viene, lista de personas, autocar, alergias, mensajes, quién no viene, quién ha
respondido varias veces, historial completo y cómo borrar datos.

1. Supabase → **SQL Editor** → **New query** → pegad **una** consulta → **Run**.
2. Encima de los resultados, botón **Export** → descargar como **CSV**.

### Abrir el CSV en Excel o Google Sheets

- **Excel** (en español): doble clic. Los CSV del panel usan `;` como separador y UTF-8 con BOM,
  así que las tildes, la ñ y las columnas salen bien.
- **Google Sheets**: Archivo → Importar → Subir → «Detectar automáticamente».
- Los CSV que exporta **Supabase** usan `,`: en Excel, mejor *Datos → Desde texto/CSV*.
- Por seguridad, cualquier texto que empiece por `=`, `+`, `-` o `@` sale con un apóstrofo delante
  (`'=…`): así Excel nunca lo ejecuta como una fórmula.

### Qué se guarda (y qué no)

| Columna | Qué es |
|---|---|
| `created_at` | Fecha y hora del envío (UTC; el panel y las consultas la muestran en hora de España) |
| `nombre` | Nombre y apellidos de quien responde |
| `asistencia` | `si` / `no` |
| `n_acompanantes`, `acompanantes` | Número y nombres de los acompañantes |
| `transporte_ida`, `transporte_vuelta` | Plazas de autocar: Iglesia de San Pablo → La Posada Real del Pinar, y La Posada Real del Pinar → Plaza del Poniente |
| `alergias` | Por persona: casillas marcadas y «otras alergias» |
| `mensaje` | «¿Algo que decirnos?» |
| `submission_id` | Identificador del envío (evita duplicados si alguien pulsa dos veces) |
| `user_agent` | Navegador usado, recortado (solo para diagnosticar problemas) |

**No se guarda** ni correo electrónico ni dirección IP.

### Si alguien responde dos veces

Cada envío es una fila nueva (nunca se sobrescribe nada). Si una persona pulsa «Modificar mi
respuesta» o vuelve a rellenar el formulario, **cuenta la última respuesta con el mismo nombre**
(sin distinguir mayúsculas, tildes ni espacios). El panel lo indica con «Ha respondido N veces» y
la consulta 8 de `consultas.sql` las lista. Si dos invitados distintos se llamaran exactamente igual,
aparecerían ahí: revisadlo con el historial.

---

## 2. Cómo funciona

```
Invitado (móvil)                       Vercel                         Supabase
┌──────────────────────┐   POST JSON   ┌───────────────────┐  HTTPS   ┌──────────────────┐
│ formulario           │ ────────────▶ │ api/rsvp.js       │ ───────▶ │ tabla rsvps      │
│ public/js/rsvp.js    │ ◀──────────── │ valida y guarda   │ ◀─────── │ (RLS, sin acceso │
└──────────────────────┘  201 / 400 …  └───────────────────┘          │  público)        │
                                        api/admin.js ── lee ───────▶ └──────────────────┘
Novios ── /admin (contraseña) ──────────▶ (ADMIN_TOKEN)
```

- El navegador **nunca** habla con Supabase: solo con `/api/rsvp` (mismo dominio). La clave secreta
  de Supabase vive únicamente en las variables de entorno de Vercel.
- El formulario valida en el navegador y **el servidor vuelve a validarlo todo** (tipos, rangos,
  longitudes, limpieza de espacios y caracteres de control, Unicode normalizado).
- Cada envío lleva un `submission_id` generado en el navegador: si llega dos veces (doble clic,
  reintento con mala cobertura), solo se guarda una.
- Si falla la red, el formulario reintenta **una vez** con el mismo `submission_id`. Si aun así no se
  puede, conserva todo lo escrito, explica qué pasa y, si habéis puesto un WhatsApp o correo
  (ver §6), ofrece **«Envíanosla por WhatsApp»** con la respuesta ya redactada.
- Mientras se rellena, se guarda un **borrador** en el navegador (por si se recarga la página);
  se borra al enviar.

---

## 3. Puesta en marcha paso a paso

### 3.1 Crear el proyecto en Supabase

1. Entrad en [supabase.com](https://supabase.com) y cread una cuenta (podéis usar la de GitHub).
2. **New project**: nombre `martayjorge`, una contraseña de base de datos (guardadla en vuestro gestor
   de contraseñas; no hará falta en la web) y una **región europea** (por ejemplo *West EU (Paris)*
   o *Central EU (Frankfurt)*).
3. Esperad un par de minutos a que termine de crearse.

### 3.2 Crear la tabla

1. Menú izquierdo → **SQL Editor** → **New query**.
2. Copiad **todo** el contenido de [`supabase/schema.sql`](../supabase/schema.sql), pegadlo y pulsad **Run**.
3. Debe decir *Success. No rows returned*. En **Table Editor** aparecerán `rsvps` (vacía) y las vistas
   `rsvp_vigentes`, `rsvp_personas` y `rsvp_resumen`.

Se puede volver a ejecutar sin perder datos. En **Advisors → Security Advisor** saldrá el aviso
*«RLS enabled, no policy»* para `rsvps`: **es lo esperado** (nadie con la clave pública puede acceder).

### 3.3 Copiar la dirección y la clave secreta

1. **Dirección del proyecto** (`SUPABASE_URL`): botón **Connect** de la parte superior, o
   **Project Settings → Data API → Project URL**. Es del estilo `https://abcdefghijkl.supabase.co`.
2. **Clave secreta** (`SUPABASE_SECRET_KEY`): **Project Settings → API Keys** → pestaña
   **Publishable and secret API keys** → sección **Secret keys** → copiar (empieza por `sb_secret_`).
   Si no aparece, pulsad **Create new API keys**.

> ⚠️ **Usad la clave nueva `sb_secret_…`, no la antigua `service_role`** (la que empieza por `eyJ`).
> Supabase retira las claves antiguas **a finales de 2026**, antes de la boda. El código acepta
> `SUPABASE_SERVICE_ROLE_KEY` solo como alternativa temporal.
>
> ⚠️ La clave secreta da acceso total a la base de datos: no la pongáis nunca en el código, ni en
> el navegador, ni la mandéis por WhatsApp o correo. Solo en Vercel.

### 3.4 Variables de entorno en Vercel

Vercel → vuestro proyecto → **Settings → Environment Variables**. Añadid (marcando *Production* y
*Preview*):

| Variable | Valor | Obligatoria |
|---|---|---|
| `SUPABASE_URL` | `https://xxxx.supabase.co` | Sí |
| `SUPABASE_SECRET_KEY` | `sb_secret_…` (marcadla como *Sensitive*) | Sí |
| `ADMIN_TOKEN` | La contraseña del panel `/admin`: **mínimo 12 caracteres**. Ej.: `pinar-sanpablo-mayo-2027` | Para usar el panel |
| `CRON_SECRET` | Cualquier texto largo y aleatorio | Recomendada (protege `/api/ping`) |

Después, **Deployments → (último) → ⋯ → Redeploy**: las variables solo se aplican en despliegues nuevos.

Opcional pero recomendable: **Settings → Functions → Function Region** → una región europea cercana
a la de Supabase (p. ej. París o Fráncfort) para que el guardado sea más rápido.

### 3.5 Probar que todo funciona

1. Abrid la web, rellenad el formulario con el nombre **«Prueba Marta»** y enviad.
2. Entrad en `/admin`: debe aparecer. También en Supabase → Table Editor → `rsvps`.
3. Borrad las pruebas antes de mandar la invitación (§5).

### 3.6 Mantener Supabase despierto (¡importante en el plan gratuito!)

El plan gratuito de Supabase **pausa los proyectos con poca actividad durante 7 días** (avisa por
correo antes). Un proyecto en pausa **no guarda confirmaciones** hasta que alguien lo reactiva.
Como las respuestas pueden llegar con semanas de calma entre medias, hay tres defensas:

1. **Cron diario de Vercel** que llama a `/api/ping` (hace una consulta mínima). Hay que añadir esto
   a `vercel.json`:
   ```json
   "crons": [{ "path": "/api/ping", "schedule": "17 9 * * *" }]
   ```
   Con `CRON_SECRET` definido, Vercel envía la cabecera necesaria automáticamente.
2. **Leed los correos de Supabase**: si avisan de una pausa, basta con entrar en el panel del proyecto.
3. Para tranquilidad total durante los meses de confirmaciones: **plan Pro** (los proyectos de pago
   no se pausan).

Si se llega a pausar: supabase.com → proyecto → **Resume project** (los datos se conservan).

---

## 4. Probar en local (desarrolladores)

Requisitos: Node 18 o superior. No hay dependencias que instalar.

```bash
npm run dev          # = MOCK_SUPABASE=1 node scripts/dev.mjs → http://127.0.0.1:3000
npm test             # pruebas de la API contra el Supabase simulado (node:test)
```

- Con `MOCK_SUPABASE=1` **no se toca ningún Supabase real**: un simulador de la API de Supabase con
  las mismas columnas y restricciones que `schema.sql` guarda en memoria y en `.dev-data/rsvps.json`
  (ignorado por git). Para vaciarlo: borrad ese fichero y reiniciad.
- Rutas útiles: `/` (la web), `/_dev/rsvp` (solo la sección del formulario, para trabajar en ella),
  `/admin` (contraseña en local: `desarrollo-local-2027`).
- El servidor aplica las cabeceras de `vercel.json` (incluida la CSP) para ver los problemas antes
  de desplegar, y recarga `api/*.js` en cada petición.
- Contra el Supabase real: copiad `.env.example` a `.env`, rellenadlo y ejecutad
  `node scripts/dev.mjs` (sin `MOCK_SUPABASE`). ¡Ojo, esos envíos se guardan de verdad!
- Puerto: `PORT=3001 npm run dev`.

---

## 5. Vaciar los datos de prueba

En Supabase → SQL Editor, usad el apartado **10** de `consultas.sql`:

```sql
select id, created_at, nombre from public.rsvps where nombre ilike '%prueba%';  -- mirad primero
delete from public.rsvps where nombre ilike '%prueba%';                          -- y luego borrad
-- o, para empezar de cero antes de mandar la invitación (¡irreversible!):
truncate table public.rsvps;
```

(Desde `/admin` no se puede borrar nada, a propósito.)

---

## 6. Ajustes opcionales

- **WhatsApp/correo de rescate**: si el envío fallara, el formulario puede ofrecer «Envíanosla por
  WhatsApp» con la respuesta ya escrita. Basta con poner el teléfono (con prefijo, sin espacios) en
  la sección `#confirmacion` de `public/index.html`: `data-whatsapp="34600111222"` (o `data-email="…"`).
  Si no se pone, usa el de la sección `#alojamiento`, si lo tiene.
- **Textos**: los mensajes de agradecimiento están en `public/index.html`, sección `#confirmacion`
  (`data-texto-si` / `data-texto-no`); los de error, al principio de `public/js/rsvp.js` (`TXT`).

---

## 7. Seguridad, privacidad y antispam

- **Base de datos cerrada**: RLS activada sin políticas; la clave pública no puede leer ni escribir.
  La clave secreta solo tiene permiso para **leer e insertar** (ni borrar ni modificar), así que aunque
  se filtrara no podrían borrar respuestas. Las vistas usan `security_invoker`.
- **Antispam sin molestar** (sin CAPTCHA): campo trampa oculto (si un robot lo rellena se le responde
  «ok» y no se guarda), tiempo mínimo de 2,5 s entre que se muestra el formulario y se envía (el
  formulario espera solo si hace falta; nunca se finge éxito a una persona), cuerpo de 20 KB como
  máximo, solo `application/json`, y `submission_id` único. Vercel ya filtra ataques masivos; si
  llegara spam se puede añadir una regla de *rate limit* en Vercel → Firewall.
- **Panel**: protegido con `ADMIN_TOKEN` (mín. 12 caracteres), comparación en tiempo constante,
  ~0,8 s de espera tras cada contraseña incorrecta, respuestas `no-store` y `noindex`. La contraseña
  viaja en la cabecera `Authorization`, nunca en la URL. Todo lo que escriben los invitados se pinta
  como texto (nunca como HTML).
- **Privacidad**: las alergias son datos de salud. Usadlas solo para organizar la boda, no compartáis
  los CSV más de lo necesario y, **después de la boda**, exportad lo que queráis conservar y vaciad la
  tabla (§5).
- **Límites**: hasta 8 acompañantes; hasta 9 plazas por trayecto y nunca más de 1 + acompañantes;
  nombre 120 caracteres, mensaje 1000, «otras alergias» 300. El panel muestra hasta 1000 envíos
  (límite por defecto de la API de Supabase; de sobra para una boda).

---

## 8. Contrato de la API (desarrolladores)

### `POST /api/rsvp` (`Content-Type: application/json`, máx. 20 KB)

```json
{
  "submission_id": "uuid generado en el navegador",
  "nombre": "Ana García López",
  "asistencia": "si",
  "acompanantes": [{ "nombre": "Luis Pérez" }],
  "transporte": { "ida": 2, "vuelta": 2 },
  "alergias": [{ "persona": "titular", "opciones": ["sin_gluten"], "otras": "" },
               { "persona": "acompanante_1", "opciones": [], "otras": "Alergia al huevo" }],
  "mensaje": "¡Qué ganas!",
  "web": "",
  "t": 12345
}
```

- `opciones` ∈ `sin_gluten`, `sin_lactosa`, `vegetariano`, `vegano`, `frutos_secos`, `marisco`.
  Solo se envían las personas con algo marcado o escrito; el servidor añade el `nombre` de cada persona.
- Con `asistencia: "no"`, acompañantes, autocar y alergias se ignoran (se guardan vacíos).

| Respuesta | Cuándo |
|---|---|
| `201 {ok:true}` | Guardada |
| `200 {ok:true, duplicado:true}` | Ese `submission_id` ya estaba guardado (no se duplica) |
| `200 {ok:true}` | Trampa antispam rellena: no se guarda |
| `400 {ok:false, errores:{campo:"mensaje"}}` | Datos no válidos. Claves: `nombre`, `asistencia`, `acompanantes`, `acompanantes.N.nombre` (N desde 0), `transporte.ida`, `transporte.vuelta`, `alergias`, `alergias.<persona>`, `alergias.<persona>.otras`, `mensaje`, `submission_id`, `general` (p. ej. envío en menos de 2,5 s) |
| `405` / `413` / `415` | Método, tamaño o tipo de contenido no admitidos |
| `503 {ok:false, error}` | Supabase caído o mal configurado (el detalle va a los logs de Vercel, nunca al invitado) |

Hacia Supabase: `POST {SUPABASE_URL}/rest/v1/rsvps?on_conflict=submission_id&select=submission_id`
con `apikey` (y `Authorization: Bearer` solo si la clave es un JWT antiguo) y
`Prefer: return=representation,resolution=ignore-duplicates`: si la fila ya existía PostgREST
devuelve `[]` y así se detecta el duplicado. Un reintento ante fallo de red o 502/503/504, con un
plazo total de ~8,5 s; no sigue redirecciones.

### `GET /api/admin`

Cabecera `Authorization: Bearer <ADMIN_TOKEN>` (el panel la envía con `encodeURIComponent` para
admitir tildes). Sin `ADMIN_TOKEN` (o con menos de 12 caracteres) → `404`; incorrecta → `401`;
correcta → `{ok, generado, resumen, respuestas, limite_alcanzado}`, donde `respuestas` son todas las
filas (más recientes primero) marcadas con `vigente` y `n_respuestas`. Los cálculos replican las
vistas de `schema.sql`.

### `GET /api/ping`

Consulta mínima para que Supabase no pause el proyecto. Si existe `CRON_SECRET`, exige
`Authorization: Bearer <CRON_SECRET>` (Vercel Cron la envía sola). No devuelve datos.

---

## 9. Ficheros

| Fichero | Qué hace |
|---|---|
| `public/index.html` (sección `#confirmacion`) | Marcado del formulario |
| `public/css/rsvp.css` · `public/js/rsvp.js` | Estilos y comportamiento del formulario |
| `public/admin/` | Panel de los novios (`index.html`, `admin.css`, `admin.js`) |
| `api/rsvp.js` · `api/admin.js` · `api/ping.js` | Funciones de Vercel |
| `api/_lib/` | Validación, acceso a Supabase y cálculos compartidos (no son funciones) |
| `supabase/schema.sql` · `supabase/consultas.sql` | Tabla, vistas y permisos · consultas útiles |
| `scripts/dev.mjs` · `scripts/test-rsvp.mjs` | Servidor de desarrollo con Supabase simulado · pruebas |
| `.env.example` | Plantilla de variables de entorno |

---

## 10. Si algo falla

- **Los invitados ven «No hemos podido enviar tu respuesta»** → Vercel → proyecto → **Logs**, función
  `/api/rsvp`. El mensaje dice la causa: *Faltan las variables…* (§3.4), *Invalid API key* (clave mal
  copiada), *No existe la tabla «rsvps»* (falta §3.2), *Faltan permisos* (volved a ejecutar
  `schema.sql`), *proyecto en pausa* (§3.6). El panel `/admin` muestra el mismo diagnóstico.
- **`/admin` dice que el panel no está activado** → falta `ADMIN_TOKEN` o tiene menos de 12 caracteres;
  tras cambiarlo, **Redeploy**.
- **Alguien no encuentra su respuesta** → mirad el historial (consulta 9): quizá escribió el nombre
  de otra forma.
