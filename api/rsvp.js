'use strict';
/**
 * POST /api/rsvp — guarda una confirmación de asistencia en Supabase.
 *
 * Cuerpo (application/json, máx. 20 KB):
 *   { submission_id, nombre, asistencia: "si"|"no", acompanantes: [{nombre}],
 *     transporte: {ida, vuelta}, alergias: [{persona, opciones, otras}],
 *     mensaje, web: "" (trampa antispam), t: ms desde que se pintó el formulario }
 *
 * Respuestas:
 *   201 {ok:true}                    guardada
 *   200 {ok:true, duplicado:true}    ese submission_id ya estaba guardado (no se duplica)
 *   200 {ok:true}                    trampa antispam rellenada: se finge éxito y no se guarda
 *   400 {ok:false, errores:{campo: "mensaje"}}   datos no válidos
 *   405 / 413 / 415                  método, tamaño o formato no admitidos
 *   503 {ok:false, error}            Supabase caído o mal configurado
 * Documentación completa: docs/rsvp.md
 */

const { enviarJSON, esJSON, leerCuerpoJSON } = require('./_lib/http');
const { validarRsvp, recortarUserAgent, LIMITES } = require('./_lib/validar');
const { leerConfig, insertarRsvp, describirError } = require('./_lib/supabase');

const ERROR_SERVICIO = 'No hemos podido guardar tu respuesta en este momento. Inténtalo de nuevo en unos minutos.';

module.exports = async function rsvp(req, res) {
  try {
    if (req.method !== 'POST') {
      return enviarJSON(res, 405, { ok: false, error: 'Método no permitido.' }, { Allow: 'POST' });
    }
    if (!esJSON(req)) {
      return enviarJSON(res, 415, { ok: false, error: 'El formato de la petición no es válido.' });
    }

    const cuerpo = await leerCuerpoJSON(req, LIMITES.cuerpoBytes);
    if (!cuerpo.ok) return enviarJSON(res, cuerpo.status, { ok: false, error: cuerpo.error });
    const entrada = cuerpo.valor;
    if (!entrada || typeof entrada !== 'object' || Array.isArray(entrada)) {
      return enviarJSON(res, 400, { ok: false, errores: { general: 'Los datos enviados no son válidos.' } });
    }

    // Trampa antispam: un campo oculto que las personas nunca rellenan.
    const trampa = entrada.web;
    if (trampa !== undefined && trampa !== null && !(typeof trampa === 'string' && trampa.trim() === '')) {
      console.warn('[rsvp] Envío descartado por la trampa antispam');
      return enviarJSON(res, 200, { ok: true });
    }

    // Antibot: nadie rellena el formulario en menos de 2,5 s. El formulario ya espera
    // ese tiempo antes de enviar, así que esto nunca debería verlo un invitado; aun así
    // no se finge éxito (para no perder jamás una respuesta real).
    if (typeof entrada.t === 'number' && Number.isFinite(entrada.t) && entrada.t >= 0 && entrada.t < LIMITES.tiempoMinimoMs) {
      return enviarJSON(res, 400, {
        ok: false,
        errores: { general: 'El formulario se ha enviado demasiado rápido. Espera un par de segundos y vuelve a intentarlo.' },
      });
    }

    const v = validarRsvp(entrada);
    if (!v.ok) return enviarJSON(res, 400, { ok: false, errores: v.errores });

    const cfg = leerConfig();
    if (!cfg.ok) {
      console.error('[rsvp] Configuración incompleta:', cfg.motivo);
      return enviarJSON(res, 503, { ok: false, error: ERROR_SERVICIO });
    }

    const fila = { ...v.datos, user_agent: recortarUserAgent(req.headers['user-agent']) };
    const resultado = await insertarRsvp(cfg, fila);

    // Log sin datos personales: solo qué tipo de respuesta ha llegado.
    console.log(`[rsvp] ${resultado.insertado ? 'guardada' : 'duplicada'}: asistencia=${fila.asistencia} personas=${fila.asistencia === 'si' ? 1 + fila.n_acompanantes : 0}`);
    return resultado.insertado
      ? enviarJSON(res, 201, { ok: true })
      : enviarJSON(res, 200, { ok: true, duplicado: true });
  } catch (err) {
    console.error('[rsvp] No se pudo guardar:', describirError(err));
    return enviarJSON(res, 503, { ok: false, error: ERROR_SERVICIO });
  }
};
