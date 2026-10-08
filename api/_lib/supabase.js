'use strict';
/**
 * Acceso mínimo a Supabase (PostgREST) con fetch, sin dependencias.
 *
 * Variables de entorno (en Vercel → Settings → Environment Variables):
 *   SUPABASE_URL          https://<proyecto>.supabase.co
 *   SUPABASE_SECRET_KEY   sb_secret_…  (recomendada)
 *   SUPABASE_SERVICE_ROLE_KEY  eyJ…    (alternativa antigua; Supabase la retira a finales de 2026)
 *
 * La clave secreta solo vive aquí, en el servidor. El navegador nunca la ve.
 */

const { pausa } = require('./http');

const COLUMNAS_LISTADO = [
  'id', 'created_at', 'nombre', 'asistencia', 'n_acompanantes', 'acompanantes',
  'transporte_ida', 'transporte_vuelta', 'alergias', 'mensaje',
].join(',');
const LIMITE_FILAS = 1000; // máximo por defecto de la API de Supabase

class ErrorSupabase extends Error {
  /**
   * @param {string} message  descripción técnica (va a los logs de Vercel, nunca al invitado)
   * @param {{status?: number, codigo?: string, diagnostico?: string, causa?: unknown}} extra
   */
  constructor(message, { status = 0, codigo = '', diagnostico = '', causa } = {}) {
    super(message);
    this.name = 'ErrorSupabase';
    this.status = status;
    this.codigo = codigo;
    this.diagnostico = diagnostico || 'No se ha podido conectar con la base de datos.';
    if (causa) this.cause = causa;
  }
}

/** Lee y comprueba la configuración. Nunca devuelve ni registra la clave. */
function leerConfig(env = process.env) {
  let url = String(env.SUPABASE_URL || '').trim().replace(/\/+$/, '');
  const clave = String(env.SUPABASE_SECRET_KEY || env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
  if (!url || !clave) {
    return { ok: false, motivo: 'Faltan las variables SUPABASE_URL y/o SUPABASE_SECRET_KEY en Vercel.' };
  }
  url = url.replace(/\/rest\/v1$/i, ''); // por si se pegó la URL de la API REST
  if (!/^https?:\/\/[^/\s?#]+(\/[^\s?#]*)?$/i.test(url)) {
    return { ok: false, motivo: 'SUPABASE_URL no es válida: debe ser como https://xxxx.supabase.co' };
  }
  if (clave.startsWith('sb_publishable_')) {
    return { ok: false, motivo: 'Se ha puesto la clave pública (sb_publishable_…); hace falta la secreta (sb_secret_…).' };
  }
  if (clave.startsWith('eyJ') && rolDelJWT(clave) === 'anon') {
    return { ok: false, motivo: 'Se ha puesto la clave «anon»; hace falta la secreta (sb_secret_…) o la service_role.' };
  }
  return { ok: true, url, clave };
}

function rolDelJWT(jwt) {
  try {
    return JSON.parse(Buffer.from(jwt.split('.')[1], 'base64url').toString('utf8')).role || '';
  } catch {
    return '';
  }
}

function cabecerasBase(clave) {
  const h = { apikey: clave, Accept: 'application/json' };
  // Las claves nuevas (sb_secret_…) NO son JWT y Supabase las rechaza en Authorization.
  if (clave.startsWith('eyJ')) h.Authorization = `Bearer ${clave}`;
  return h;
}

/**
 * Petición a PostgREST con 1 reintento ante fallo de red o 502/503/504,
 * todo dentro de un plazo total (las funciones de Vercel tienen tiempo limitado).
 */
async function peticion(cfg, ruta, { method = 'GET', headers = {}, body, plazoMs = 8500 } = {}) {
  const fin = Date.now() + plazoMs;
  let ultimoError;
  for (let intento = 0; intento < 2; intento++) {
    const restante = fin - Date.now();
    if (intento > 0 && restante < 1500) break;
    try {
      const r = await fetch(cfg.url + ruta, {
        method,
        body,
        headers: { ...cabecerasBase(cfg.clave), ...headers },
        redirect: 'error', // nunca reenviar la clave a otra dirección
        signal: AbortSignal.timeout(Math.max(1000, Math.min(6000, restante))),
      });
      if (intento === 0 && (r.status === 502 || r.status === 503 || r.status === 504)) {
        await r.arrayBuffer().catch(() => {});
        await pausa(350);
        continue;
      }
      return r;
    } catch (err) {
      ultimoError = err;
      if (intento === 0) await pausa(350);
    }
  }
  const tiempo = ultimoError && (ultimoError.name === 'TimeoutError' || ultimoError.name === 'AbortError');
  const codigoRed = (ultimoError && ultimoError.cause && ultimoError.cause.code) || '';
  throw new ErrorSupabase(
    `Sin respuesta de Supabase (${tiempo ? 'tiempo agotado' : (codigoRed || (ultimoError && ultimoError.name) || 'error de red')})`,
    {
      codigo: codigoRed,
      diagnostico: tiempo
        ? 'Supabase no responde. ¿Está el proyecto en pausa? Entra en supabase.com y pulsa «Resume project».'
        : 'No se puede conectar con Supabase. Revisa SUPABASE_URL o si el proyecto está en pausa.',
      causa: ultimoError,
    },
  );
}

/** Traduce una respuesta de error de PostgREST a algo comprensible (sin datos de invitados). */
async function errorDesdeRespuesta(r) {
  let codigo = '';
  let mensaje = '';
  try {
    const texto = (await r.text()).slice(0, 2000);
    const j = JSON.parse(texto);
    codigo = String(j.code || '');
    mensaje = String(j.message || j.msg || j.error || '');
  } catch { /* cuerpo vacío o no JSON */ }
  let diagnostico;
  if (r.status === 540) {
    diagnostico = 'El proyecto de Supabase está en pausa. Entra en supabase.com y pulsa «Resume project».';
  } else if (r.status === 401 || /api key|jwt/i.test(mensaje)) {
    diagnostico = 'La clave de Supabase no es válida. Revisa SUPABASE_SECRET_KEY en Vercel.';
  } else if (codigo === 'PGRST205' || codigo === '42P01' || r.status === 404) {
    diagnostico = 'No existe la tabla «rsvps». Ejecuta supabase/schema.sql en el SQL Editor de Supabase.';
  } else if (codigo === '42501' || r.status === 403) {
    diagnostico = 'Faltan permisos en la base de datos. Vuelve a ejecutar supabase/schema.sql.';
  } else if (codigo === '23514' || codigo === '22P02' || codigo === '23502') {
    diagnostico = 'La base de datos ha rechazado los datos (regla de validación). Revisa que schema.sql esté actualizado.';
  } else {
    diagnostico = 'Supabase ha devuelto un error inesperado.';
  }
  // El «message» de PostgREST describe el esquema (tabla, restricción), no los datos del invitado;
  // el campo «details» (que sí los incluye) se descarta a propósito.
  return new ErrorSupabase(`PostgREST HTTP ${r.status}${codigo ? ' ' + codigo : ''}: ${mensaje.slice(0, 200)}`, {
    status: r.status, codigo, diagnostico,
  });
}

/**
 * Inserta una respuesta. Idempotente por submission_id:
 *   { insertado: true }  → fila nueva
 *   { insertado: false } → ese submission_id ya existía (duplicado), no se toca nada
 */
async function insertarRsvp(cfg, fila) {
  const r = await peticion(cfg, '/rest/v1/rsvps?on_conflict=submission_id&select=submission_id', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // return=representation: si la fila era duplicada, PostgREST devuelve [] (así lo detectamos)
      Prefer: 'return=representation,resolution=ignore-duplicates',
    },
    body: JSON.stringify(fila),
  });
  if (r.status === 201 || r.status === 200) {
    let datos = null;
    try { datos = JSON.parse(await r.text()); } catch { /* sin cuerpo */ }
    return { insertado: Array.isArray(datos) ? datos.length > 0 : true };
  }
  if (r.status === 409) {
    const err = await errorDesdeRespuesta(r);
    if (err.codigo === '23505') return { insertado: false }; // clave única: ya estaba guardada
    throw err;
  }
  throw await errorDesdeRespuesta(r);
}

/** Todas las respuestas (más recientes primero). */
async function listarRsvps(cfg) {
  const ruta = `/rest/v1/rsvps?select=${COLUMNAS_LISTADO}&order=created_at.desc,id.desc&limit=${LIMITE_FILAS}`;
  const r = await peticion(cfg, ruta);
  if (r.status !== 200) throw await errorDesdeRespuesta(r);
  const datos = await r.json().catch(() => null);
  if (!Array.isArray(datos)) throw new ErrorSupabase('Respuesta inesperada de PostgREST (no es una lista)');
  return { filas: datos, limiteAlcanzado: datos.length >= LIMITE_FILAS };
}

/** Consulta mínima para mantener el proyecto activo (ver api/ping.js). */
async function comprobarConexion(cfg) {
  const r = await peticion(cfg, '/rest/v1/rsvps?select=id&limit=1');
  if (r.status !== 200) throw await errorDesdeRespuesta(r);
  await r.arrayBuffer().catch(() => {});
  return true;
}

/** Descripción del error apta para los logs (sin claves ni datos personales). */
function describirError(err) {
  if (!err) return 'error desconocido';
  if (err instanceof ErrorSupabase) return `${err.message} → ${err.diagnostico}`;
  return `${err.name || 'Error'}: ${String(err.message || '').slice(0, 200)}`;
}

module.exports = {
  ErrorSupabase,
  leerConfig,
  insertarRsvp,
  listarRsvps,
  comprobarConexion,
  describirError,
  LIMITE_FILAS,
};
