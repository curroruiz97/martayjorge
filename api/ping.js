'use strict';
/**
 * GET /api/ping — mantiene despierto el proyecto de Supabase.
 *
 * El plan gratuito de Supabase pausa los proyectos con poca actividad durante
 * 7 días; si pasara en plena temporada de confirmaciones, el formulario dejaría
 * de guardar. Un cron diario de Vercel llama aquí y hace una consulta mínima.
 * (Configuración del cron: docs/rsvp.md → «Mantener Supabase despierto»).
 *
 * Si existe la variable CRON_SECRET, Vercel la envía sola como
 * «Authorization: Bearer …» y se exige. No devuelve ningún dato.
 */

const { enviarJSON, leerBearer, mismoSecreto } = require('./_lib/http');
const { leerConfig, comprobarConexion, describirError } = require('./_lib/supabase');

module.exports = async function ping(req, res) {
  if (req.method !== 'GET') {
    return enviarJSON(res, 405, { ok: false }, { Allow: 'GET' });
  }
  const secreto = String(process.env.CRON_SECRET || '').trim();
  if (secreto && !mismoSecreto(leerBearer(req), secreto)) {
    return enviarJSON(res, 401, { ok: false });
  }
  const cfg = leerConfig();
  if (!cfg.ok) {
    console.error('[ping] Configuración incompleta:', cfg.motivo);
    return enviarJSON(res, 503, { ok: false });
  }
  try {
    await comprobarConexion(cfg);
    return enviarJSON(res, 200, { ok: true });
  } catch (err) {
    console.error('[ping] Supabase no responde:', describirError(err));
    return enviarJSON(res, 503, { ok: false });
  }
};
