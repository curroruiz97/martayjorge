'use strict';
/**
 * GET /api/admin — datos para el panel de los novios (/admin).
 *
 * Protegido con la variable de entorno ADMIN_TOKEN (mínimo 12 caracteres), que
 * se envía como «Authorization: Bearer <token>» (nunca en la URL).
 *   · Sin ADMIN_TOKEN (o demasiado corto) → 404: el panel no existe.
 *   · Token incorrecto → espera ~0,8 s y 401.
 *   · Correcto → { ok, generado, resumen, respuestas, limite_alcanzado }
 *     «respuestas» son TODAS las filas (más recientes primero) marcadas con
 *     vigente (última respuesta de esa persona) y n_respuestas.
 */

const { enviarJSON, pausa, leerBearer, mismoSecreto } = require('./_lib/http');
const { leerConfig, listarRsvps, describirError, ErrorSupabase } = require('./_lib/supabase');
const { marcarVigentes, calcularResumen } = require('./_lib/resumen');

const LONGITUD_MINIMA = 12;
const CABECERAS = {
  'Cache-Control': 'no-store, private',
  'X-Robots-Tag': 'noindex, nofollow',
  'Referrer-Policy': 'no-referrer',
  Vary: 'Authorization',
};

module.exports = async function admin(req, res) {
  try {
    const token = String(process.env.ADMIN_TOKEN || '').trim();
    if (token.length < LONGITUD_MINIMA) {
      if (token) console.warn(`[admin] ADMIN_TOKEN tiene menos de ${LONGITUD_MINIMA} caracteres: el panel queda desactivado.`);
      return enviarJSON(res, 404, { ok: false, error: 'No encontrado.' }, CABECERAS);
    }
    if (req.method !== 'GET') {
      return enviarJSON(res, 405, { ok: false, error: 'Método no permitido.' }, { ...CABECERAS, Allow: 'GET' });
    }

    const enviado = leerBearer(req);
    if (!enviado || !mismoSecreto(enviado, token)) {
      await pausa(600 + Math.floor(Math.random() * 400)); // frena los intentos a ciegas
      return enviarJSON(res, 401, { ok: false, error: 'Contraseña incorrecta.' }, { ...CABECERAS, 'WWW-Authenticate': 'Bearer' });
    }

    const cfg = leerConfig();
    if (!cfg.ok) {
      console.error('[admin] Configuración incompleta:', cfg.motivo);
      return enviarJSON(res, 503, { ok: false, error: cfg.motivo }, CABECERAS);
    }

    const { filas, limiteAlcanzado } = await listarRsvps(cfg);
    const respuestas = marcarVigentes(filas);
    return enviarJSON(res, 200, {
      ok: true,
      generado: new Date().toISOString(),
      resumen: calcularResumen(respuestas),
      respuestas,
      limite_alcanzado: limiteAlcanzado,
    }, CABECERAS);
  } catch (err) {
    console.error('[admin]', describirError(err));
    // Quien llega aquí ya ha demostrado conocer la contraseña: se le da un diagnóstico útil.
    const error = err instanceof ErrorSupabase ? err.diagnostico : 'Ha ocurrido un error inesperado.';
    return enviarJSON(res, 503, { ok: false, error }, CABECERAS);
  }
};
