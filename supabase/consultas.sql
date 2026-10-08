-- =============================================================================
--  Marta y Jorge · Consultas listas para el SQL Editor de Supabase
-- -----------------------------------------------------------------------------
--  CÓMO USARLAS
--    Supabase → SQL Editor → «New query» → pega UNA consulta → «Run».
--    Para descargarla: encima de los resultados, botón «Export» → CSV
--    (se abre con Excel, Numbers o Google Sheets).
--
--  Todas son de SOLO LECTURA salvo las del apartado 10 (borrar), que van
--  comentadas con «--» para que no se ejecuten por accidente.
--  Las fechas se muestran en hora de España (Europe/Madrid).
--  «Vigente» = la última respuesta de cada persona (si alguien modificó su
--  respuesta, solo cuenta la última; ver supabase/schema.sql).
-- =============================================================================


-- 1) RESUMEN: totales de personas, autocar y alergias ---------------------------
select * from public.rsvp_resumen;


-- 2) QUIÉN VIENE: una fila por respuesta «sí», con sus acompañantes -------------
select
  nombre               as "Nombre",
  personas             as "Personas",
  acompanantes_nombres as "Acompañantes",
  transporte_ida       as "Autocar ida",
  transporte_vuelta    as "Autocar vuelta",
  alergias_detalle     as "Alergias",
  mensaje              as "Mensaje",
  to_char(created_at at time zone 'Europe/Madrid', 'DD/MM/YYYY HH24:MI') as "Respondió"
from public.rsvp_vigentes
where asistencia = 'si'
order by nombre_normalizado;


-- 3) TODAS LAS PERSONAS QUE ASISTEN (invitados + acompañantes), una por fila -----
--    Ideal para las mesas y para el catering.
select
  persona        as "Persona",
  tipo           as "Tipo",
  de_parte_de    as "De parte de",
  alergias       as "Alergias",
  otras_alergias as "Otras alergias"
from public.rsvp_personas;


-- 4) AUTOCAR: quién necesita plaza en cada trayecto ------------------------------
select
  nombre            as "Nombre",
  personas          as "Personas del grupo",
  transporte_ida    as "Ida: San Pablo → La Posada",
  transporte_vuelta as "Vuelta: La Posada → Pza. Poniente"
from public.rsvp_vigentes
where asistencia = 'si' and (transporte_ida > 0 or transporte_vuelta > 0)
order by nombre_normalizado;

-- 4b) AUTOCAR: total de plazas por trayecto
select
  coalesce(sum(transporte_ida), 0)    as "Plazas ida",
  coalesce(sum(transporte_vuelta), 0) as "Plazas vuelta"
from public.rsvp_vigentes
where asistencia = 'si';


-- 5) ALERGIAS E INTOLERANCIAS: solo las personas que tienen alguna ---------------
select
  persona        as "Persona",
  de_parte_de    as "De parte de",
  alergias       as "Alergias",
  otras_alergias as "Otras alergias"
from public.rsvp_personas
where alergias <> '' or otras_alergias <> '';


-- 6) MENSAJES que os han dejado (lo más reciente primero) ------------------------
select
  to_char(created_at at time zone 'Europe/Madrid', 'DD/MM/YYYY HH24:MI') as "Fecha",
  nombre  as "Nombre",
  case asistencia when 'si' then 'Sí' else 'No' end as "¿Asiste?",
  mensaje as "Mensaje"
from public.rsvp_vigentes
where mensaje <> ''
order by created_at desc;


-- 7) QUIÉN NO PUEDE VENIR --------------------------------------------------------
select
  nombre  as "Nombre",
  mensaje as "Mensaje",
  to_char(created_at at time zone 'Europe/Madrid', 'DD/MM/YYYY HH24:MI') as "Respondió"
from public.rsvp_vigentes
where asistencia = 'no'
order by nombre_normalizado;


-- 8) PERSONAS QUE HAN RESPONDIDO MÁS DE UNA VEZ ----------------------------------
--    Normalmente es alguien que pulsó «Modificar mi respuesta»: cuenta la última.
--    Si fueran dos personas distintas con el mismo nombre, aparecerían aquí:
--    revisadlo con el historial (consulta 9).
select
  nombre       as "Nombre (última respuesta)",
  n_respuestas as "Veces que ha respondido",
  case asistencia when 'si' then 'Sí' else 'No' end as "¿Asiste? (última)",
  to_char(created_at at time zone 'Europe/Madrid', 'DD/MM/YYYY HH24:MI') as "Última respuesta"
from public.rsvp_vigentes
where n_respuestas > 1
order by nombre_normalizado;


-- 9) HISTORIAL COMPLETO: todas las respuestas recibidas, también las modificadas --
--    (también sirve de copia de seguridad: exportadla a CSV de vez en cuando)
select
  to_char(created_at at time zone 'Europe/Madrid', 'DD/MM/YYYY HH24:MI:SS') as "Fecha",
  nombre            as "Nombre",
  asistencia        as "Asistencia",
  n_acompanantes    as "Acompañantes",
  acompanantes      as "Nombres acompañantes (JSON)",
  transporte_ida    as "Autocar ida",
  transporte_vuelta as "Autocar vuelta",
  alergias          as "Alergias (JSON)",
  mensaje           as "Mensaje",
  id
from public.rsvps
order by lower(nombre), created_at desc;


-- 10) BORRAR DATOS (¡con cuidado!) -----------------------------------------------
--    Para usarlas, quita los «--» del principio de la línea que quieras ejecutar.
--    Primero mirad SIEMPRE qué se va a borrar con la «select» de cada caso.
--
--    a) Respuestas de prueba (por ejemplo, las que tienen «prueba» en el nombre):
-- select id, created_at, nombre from public.rsvps where nombre ilike '%prueba%';
-- delete from public.rsvps where nombre ilike '%prueba%';
--
--    b) Una respuesta concreta (copiad su «id» de la consulta 9):
-- delete from public.rsvps where id = '00000000-0000-0000-0000-000000000000';
--
--    c) VACIAR TODO: antes de enviar la invitación (para quitar las pruebas) o
--       después de la boda (para no guardar datos personales más de lo necesario).
--       ¡No se puede deshacer! Exportad antes la consulta 9 a CSV.
-- truncate table public.rsvps;
