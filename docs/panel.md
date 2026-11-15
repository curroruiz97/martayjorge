# Panel de invitados (`/panel`)

> **Para Marta y Jorge**
>
> 1. Entrad en **`https://vuestro-dominio/panel`** (también desde el móvil).
> 2. Escribid vuestro **correo y contraseña**. Con «Mantener la sesión iniciada» no tendréis que volver a escribirla
>    en ese dispositivo.
> 3. Veréis cuántas personas vienen, quién ha respondido, el autocar, las alergias y los mensajes. Pulsad en
>    cualquier invitado para ver su ficha completa. Los botones **«Respuestas (Excel)»** y **«Lista por persona»**
>    descargan los datos para el catering o las mesas.

## Qué muestra

- **Totales**: personas que vienen (con acompañantes), respuestas «sí» / «no», plazas de autocar de ida
  (San Pablo → La Posada) y de vuelta (La Posada → Plaza del Poniente) y personas con alergias o dieta.
- **Confirmaciones en el tiempo**: cuántas personas han confirmado, acumulado por día.
- **Alergias e intolerancias**: cuántas personas tienen cada una.
- **Invitados**: tabla con buscador (también busca acompañantes), filtros (vienen, no vienen, con alergias,
  con autocar, con mensaje), orden por nombre, personas o fecha y una ficha por invitado con sus acompañantes,
  alergias de cada uno, autocar y mensaje. «Ver respuestas antiguas» enseña también las respuestas que alguien
  sustituyó al volver a responder (cuenta siempre la última).
- Se actualiza solo cada 5 minutos y al volver a la pestaña; el botón «Actualizar» lo hace al momento.

## Dar acceso a alguien (lo hace quien administra Supabase)

Hacen falta **dos cosas** por persona; sin cualquiera de ellas no entra:

1. **Una cuenta**: Supabase → proyecto `martayjorge` → **Authentication → Users → Add user → Create new user**.
   Escribid el correo y una contraseña, marcad **«Auto Confirm User»** y pulsad *Create user*.
2. **Estar en la lista de acceso**: Supabase → **SQL Editor** →

   ```sql
   insert into public.panel_acceso (email, nombre) values ('marta@ejemplo.com', 'Marta');
   ```

   (el correo, en minúsculas; el nombre es el del saludo «Hola, Marta»). También se puede añadir una fila en
   **Table Editor → panel_acceso**.

Quitar el acceso: `delete from public.panel_acceso where email = 'correo@ejemplo.com';` (y, si queréis, borrar la
cuenta en Authentication → Users).

**Cambiar una contraseña olvidada**: Authentication → Users → la persona → **⋯ → Change password** (o *Send
password recovery*, que solo funciona si el proyecto tiene configurado el envío de correos).

**Recomendado**: Authentication → **Sign In / Providers** → desactivad **«Allow new users to sign up»**. El panel
ya no deja ver nada a quien no esté en `panel_acceso`, pero así nadie puede ni siquiera crearse una cuenta.

## Cómo funciona (seguridad)

```
Navegador (/panel) ──▶ /api/panel (Vercel) ──▶ Supabase Auth  (¿correo y contraseña correctos?)
                                           ──▶ panel_acceso   (¿está en la lista?)
                                           ──▶ rsvps          (los datos, con la clave secreta)
```

- El navegador **nunca** habla con Supabase ni ve la clave secreta: solo con `/api/panel`, en el mismo dominio.
  Las tablas siguen sin poder leerse con la clave pública (RLS sin políticas).
- Cada petición de datos comprueba la sesión con Supabase Auth **y** que el correo esté en `panel_acceso`.
- Contraseña incorrecta → ~0,8 s de espera y el mismo mensaje exista o no el correo.
- La sesión (token de acceso de 1 hora + token de renovación) se guarda en el navegador: en `localStorage` con
  «Mantener la sesión iniciada», o solo en esa pestaña si no. «Salir» la cierra también en Supabase.
- Todo lo que escriben los invitados se pinta como texto, nunca como HTML. Respuestas `no-store` y `noindex`.

### API

| Petición | Cuerpo / cabecera | Respuesta |
|---|---|---|
| `POST /api/panel?accion=entrar` | `{ email, password }` | `200 { ok, sesion, usuario }` · `401` credenciales · `403` sin acceso |
| `POST /api/panel?accion=renovar` | `{ refresh_token }` | igual que entrar |
| `POST /api/panel?accion=salir` | `Authorization: Bearer <access_token>` | `200 { ok }` |
| `GET /api/panel` | `Authorization: Bearer <access_token>` | `200 { ok, usuario, generado, resumen, respuestas, limite_alcanzado }` |

`sesion` = `{ access_token, refresh_token, expires_at }`. `respuestas` son todas las filas (más recientes primero)
marcadas con `vigente` y `n_respuestas`; los totales replican las vistas de `supabase/schema.sql`.

## En local

`npm run dev` → `http://127.0.0.1:3000/panel` con Supabase **simulado**: `marta@ejemplo.com` o
`jorge@ejemplo.com`, contraseña `desarrollo-local-2027` (`intruso@ejemplo.com` tiene cuenta pero no está en la
lista de acceso, para probar el «no tienes acceso»).

## Si algo falla

- **«Correo o contraseña incorrectos»** → comprobad el usuario en Authentication → Users (¿confirmado?) o
  cambiad la contraseña.
- **«Esta cuenta no tiene acceso al panel»** → falta su correo en `panel_acceso` (en minúsculas).
- **«No existe la tabla panel_acceso»** → ejecutad `supabase/schema.sql` (apartado 7) en el SQL Editor.
- **«Demasiados intentos seguidos»** → Supabase limita los inicios de sesión fallidos; esperad unos minutos.
- Cualquier otro error → Vercel → Logs, función `/api/panel`.
