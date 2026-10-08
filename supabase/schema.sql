-- =============================================================================
--  Marta y Jorge · Confirmaciones de asistencia (RSVP) · esquema de Supabase
-- -----------------------------------------------------------------------------
--  CÓMO USARLO
--    Supabase → SQL Editor → «New query» → pega TODO este fichero → «Run».
--    Se puede volver a ejecutar sin perder datos: no borra nada.
--
--  QUÉ CREA
--    · public.rsvps          tabla con TODAS las respuestas (una fila por envío).
--    · public.rsvp_vigentes  vista: la última respuesta de cada persona.
--    · public.rsvp_personas  vista: una fila por cada persona que asiste
--                            (invitado + acompañantes) con sus alergias.
--    · public.rsvp_resumen   vista: totales (personas, autocar, alergias…).
--
--  SEGURIDAD
--    · RLS activada y SIN políticas, a propósito: con la clave pública
--      (publishable/anon) no se puede leer ni escribir nada. El navegador nunca
--      habla con Supabase; solo lo hacen api/rsvp.js y api/admin.js desde Vercel
--      con la clave secreta (sb_secret_… o la antigua service_role).
--      El aviso «RLS enabled, no policy» del Security Advisor es esperado.
--    · Permisos explícitos (Supabase está dejando de darlos por defecto).
--    · No se guarda correo electrónico ni dirección IP.
--
--  Si en el futuro cambias la definición de alguna vista y «Run» da error,
--  ejecuta antes:
--    drop view if exists public.rsvp_resumen, public.rsvp_personas, public.rsvp_vigentes;
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Tabla de respuestas
--    Si alguien pulsa «Modificar mi respuesta» y vuelve a enviar, se guarda una
--    fila NUEVA (nunca se sobrescribe nada); rsvp_vigentes se queda con la última.
-- -----------------------------------------------------------------------------
create table if not exists public.rsvps (
  id                uuid        primary key default gen_random_uuid(),
  created_at        timestamptz not null default now(),
  submission_id     uuid        not null,
  nombre            text        not null,
  asistencia        text        not null,
  n_acompanantes    smallint    not null default 0,
  acompanantes      jsonb       not null default '[]'::jsonb,
  transporte_ida    smallint    not null default 0,
  transporte_vuelta smallint    not null default 0,
  alergias          jsonb       not null default '[]'::jsonb,
  mensaje           text        not null default '',
  user_agent        text,

  -- Idempotencia: el navegador genera un submission_id por envío; si llega dos
  -- veces (doble clic, reintento por mala cobertura) solo se guarda una.
  constraint rsvps_submission_id_key unique (submission_id),

  constraint rsvps_nombre_chk
    check (char_length(btrim(nombre)) between 1 and 120),
  constraint rsvps_asistencia_chk
    check (asistencia in ('si', 'no')),
  constraint rsvps_n_acompanantes_chk
    check (n_acompanantes between 0 and 8),
  constraint rsvps_acompanantes_chk
    check (case when jsonb_typeof(acompanantes) = 'array'
                then jsonb_array_length(acompanantes) = n_acompanantes
                else false end),
  constraint rsvps_transporte_chk
    check (transporte_ida between 0 and 9
           and transporte_vuelta between 0 and 9
           and transporte_ida <= n_acompanantes + 1
           and transporte_vuelta <= n_acompanantes + 1),
  constraint rsvps_alergias_chk
    check (case when jsonb_typeof(alergias) = 'array'
                then jsonb_array_length(alergias) <= n_acompanantes + 1
                else false end),
  constraint rsvps_mensaje_chk
    check (char_length(mensaje) <= 1000),
  constraint rsvps_user_agent_chk
    check (user_agent is null or char_length(user_agent) <= 300),
  -- Quien no asiste no trae acompañantes, ni plazas de autocar, ni alergias.
  constraint rsvps_no_asiste_chk
    check (asistencia = 'si'
           or (n_acompanantes = 0 and transporte_ida = 0
               and transporte_vuelta = 0 and alergias = '[]'::jsonb))
);

create index if not exists rsvps_created_at_idx on public.rsvps (created_at desc);

comment on table  public.rsvps is
  'Confirmaciones de asistencia de la boda (una fila por envío). Para ver la última respuesta de cada persona usa la vista rsvp_vigentes.';
comment on column public.rsvps.created_at        is 'Fecha y hora del envío (UTC).';
comment on column public.rsvps.submission_id     is 'Identificador único del envío generado en el navegador (evita duplicados).';
comment on column public.rsvps.nombre            is 'Nombre y apellidos de quien responde.';
comment on column public.rsvps.asistencia        is 'si = asistirá · no = no podrá asistir.';
comment on column public.rsvps.n_acompanantes    is 'Número de acompañantes (sin contar a quien responde).';
comment on column public.rsvps.acompanantes      is 'Lista de acompañantes: [{"nombre": "…"}].';
comment on column public.rsvps.transporte_ida    is 'Plazas de autocar: Iglesia de San Pablo → La Posada Real del Pinar.';
comment on column public.rsvps.transporte_vuelta is 'Plazas de autocar: La Posada Real del Pinar → Plaza del Poniente.';
comment on column public.rsvps.alergias          is 'Alergias por persona: [{"persona": "titular|acompanante_N", "nombre": "…", "opciones": [...], "otras": "…"}].';
comment on column public.rsvps.mensaje           is '«¿Algo que decirnos?» (opcional).';
comment on column public.rsvps.user_agent        is 'Navegador usado (recortado), solo para diagnosticar problemas.';


-- -----------------------------------------------------------------------------
-- 2. Seguridad: RLS sin políticas + permisos mínimos
-- -----------------------------------------------------------------------------
alter table public.rsvps enable row level security;

-- La clave secreta solo puede LEER e INSERTAR: aunque se filtrara, nadie podría
-- borrar ni cambiar respuestas desde fuera. (Desde el panel de Supabase, que
-- usa el rol postgres, sí se puede borrar: ver supabase/consultas.sql).
revoke all on table public.rsvps from anon, authenticated, service_role;
grant select, insert on table public.rsvps to service_role;


-- -----------------------------------------------------------------------------
-- 3. Vista rsvp_vigentes: la última respuesta de cada persona
--    «Misma persona» = mismo nombre normalizado (minúsculas, sin tildes ni
--    diéresis, ñ→n, espacios repetidos colapsados). n_respuestas > 1 indica que
--    esa persona respondió varias veces (p. ej. modificó su respuesta).
-- -----------------------------------------------------------------------------
create or replace view public.rsvp_vigentes
with (security_invoker = true) as
with normalizadas as (
  select
    r.*,
    btrim(regexp_replace(
      translate(lower(r.nombre),
        'áàâäãåāéèêëēíìîïīóòôöõōúùûüūýÿñçÁÀÂÄÃÅĀÉÈÊËĒÍÌÎÏĪÓÒÔÖÕŌÚÙÛÜŪÝŸÑÇ',
        'aaaaaaaeeeeeiiiiioooooouuuuuyyncaaaaaaaeeeeeiiiiioooooouuuuuyync'),
      '\s+', ' ', 'g')) as nombre_normalizado
  from public.rsvps r
),
contadas as (
  select n.*, count(*) over (partition by n.nombre_normalizado) as n_respuestas
  from normalizadas n
)
select distinct on (c.nombre_normalizado)
  c.created_at,
  c.nombre,
  c.asistencia,
  case when c.asistencia = 'si' then 1 + c.n_acompanantes else 0 end as personas,
  c.n_acompanantes,
  coalesce((
    select string_agg(x.elem ->> 'nombre', ', ' order by x.idx)
    from jsonb_array_elements(c.acompanantes) with ordinality as x(elem, idx)
  ), '') as acompanantes_nombres,
  c.transporte_ida,
  c.transporte_vuelta,
  coalesce((
    select string_agg(
      coalesce(nullif(a.elem ->> 'nombre', ''), a.elem ->> 'persona') || ': ' ||
      concat_ws('; ',
        nullif((
          select string_agg(
            case o.op
              when 'sin_gluten'   then 'sin gluten / celiaquía'
              when 'sin_lactosa'  then 'sin lactosa'
              when 'vegetariano'  then 'vegetariano'
              when 'vegano'       then 'vegano'
              when 'frutos_secos' then 'alergia a frutos secos'
              when 'marisco'      then 'alergia a marisco'
              else o.op
            end, ', ' order by o.idx)
          from jsonb_array_elements_text(coalesce(a.elem -> 'opciones', '[]'::jsonb))
               with ordinality as o(op, idx)
        ), ''),
        nullif(a.elem ->> 'otras', '')),
      ' · ' order by a.idx)
    from jsonb_array_elements(c.alergias) with ordinality as a(elem, idx)
  ), '') as alergias_detalle,
  c.mensaje,
  c.n_respuestas,
  c.nombre_normalizado,
  c.acompanantes,
  c.alergias,
  c.id,
  c.submission_id
from contadas c
order by c.nombre_normalizado, c.created_at desc, c.id desc;

comment on view public.rsvp_vigentes is
  'Última respuesta de cada persona (agrupando por nombre normalizado). Úsala para contar invitados.';


-- -----------------------------------------------------------------------------
-- 4. Vista rsvp_personas: una fila por persona que asiste (para catering,
--    mesas, autocar…). Solo cuenta respuestas vigentes con asistencia = 'si'.
-- -----------------------------------------------------------------------------
create or replace view public.rsvp_personas
with (security_invoker = true) as
select
  p.persona,
  case when p.orden = 0 then 'Invitado/a' else 'Acompañante' end as tipo,
  vg.nombre as de_parte_de,
  coalesce(al.opciones, '') as alergias,
  coalesce(al.otras, '')    as otras_alergias,
  vg.created_at             as respondido,
  p.orden
from public.rsvp_vigentes vg
cross join lateral (
  select 0 as orden, vg.nombre as persona, 'titular'::text as clave
  union all
  select x.idx::int, x.elem ->> 'nombre', 'acompanante_' || x.idx
  from jsonb_array_elements(vg.acompanantes) with ordinality as x(elem, idx)
) p
left join lateral (
  select
    (select string_agg(
       case o.op
         when 'sin_gluten'   then 'sin gluten / celiaquía'
         when 'sin_lactosa'  then 'sin lactosa'
         when 'vegetariano'  then 'vegetariano'
         when 'vegano'       then 'vegano'
         when 'frutos_secos' then 'alergia a frutos secos'
         when 'marisco'      then 'alergia a marisco'
         else o.op
       end, ', ' order by o.idx)
     from jsonb_array_elements_text(coalesce(a.elem -> 'opciones', '[]'::jsonb))
          with ordinality as o(op, idx)) as opciones,
    nullif(a.elem ->> 'otras', '') as otras
  from jsonb_array_elements(vg.alergias) as a(elem)
  where a.elem ->> 'persona' = p.clave
  limit 1
) al on true
where vg.asistencia = 'si'
order by vg.nombre_normalizado, p.orden;

comment on view public.rsvp_personas is
  'Una fila por cada persona que asiste (invitado y acompañantes) con sus alergias.';


-- -----------------------------------------------------------------------------
-- 5. Vista rsvp_resumen: totales en una sola fila
-- -----------------------------------------------------------------------------
create or replace view public.rsvp_resumen
with (security_invoker = true) as
with vg as (
  select * from public.rsvp_vigentes
),
al as (
  select e.elem
  from vg
  cross join lateral jsonb_array_elements(vg.alergias) as e(elem)
  where vg.asistencia = 'si'
)
select
  (select count(*) from public.rsvps)                                          as respuestas_recibidas,
  (select count(*) from vg)                                                    as respuestas_vigentes,
  (select count(*) from vg where asistencia = 'si')                            as confirman_si,
  (select count(*) from vg where asistencia = 'no')                            as no_asisten,
  (select coalesce(sum(personas), 0) from vg)                                  as personas_asisten,
  (select coalesce(sum(n_acompanantes), 0) from vg where asistencia = 'si')    as acompanantes,
  (select coalesce(sum(transporte_ida), 0) from vg where asistencia = 'si')    as plazas_ida,
  (select coalesce(sum(transporte_vuelta), 0) from vg where asistencia = 'si') as plazas_vuelta,
  (select count(*) from al where al.elem -> 'opciones' ? 'sin_gluten')         as sin_gluten,
  (select count(*) from al where al.elem -> 'opciones' ? 'sin_lactosa')        as sin_lactosa,
  (select count(*) from al where al.elem -> 'opciones' ? 'vegetariano')        as vegetariano,
  (select count(*) from al where al.elem -> 'opciones' ? 'vegano')             as vegano,
  (select count(*) from al where al.elem -> 'opciones' ? 'frutos_secos')       as frutos_secos,
  (select count(*) from al where al.elem -> 'opciones' ? 'marisco')            as marisco,
  (select count(*) from al where coalesce(al.elem ->> 'otras', '') <> '')      as otras_alergias,
  (select count(*) from al)                                                    as personas_con_alergias;

comment on view public.rsvp_resumen is
  'Totales: respuestas, personas que asisten (con acompañantes), no asisten, plazas de autocar y alergias.';


-- -----------------------------------------------------------------------------
-- 6. Permisos de las vistas (security_invoker: aplican los permisos y la RLS
--    de quien consulta, así que con la clave pública tampoco se ve nada).
-- -----------------------------------------------------------------------------
revoke all on table public.rsvp_vigentes, public.rsvp_personas, public.rsvp_resumen
  from anon, authenticated, service_role;
grant select on table public.rsvp_vigentes, public.rsvp_personas, public.rsvp_resumen
  to service_role;
