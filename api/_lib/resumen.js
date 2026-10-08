'use strict';
/**
 * Cálculos del panel de los novios. Replican EXACTAMENTE las vistas de
 * supabase/schema.sql (rsvp_vigentes y rsvp_resumen) para que el panel /admin y
 * el SQL Editor de Supabase den siempre los mismos números.
 */

const { OPCIONES_ALERGIA } = require('./validar');

// Mismo mapa que translate(...) en schema.sql.
const DE = 'áàâäãåāéèêëēíìîïīóòôöõōúùûüūýÿñçÁÀÂÄÃÅĀÉÈÊËĒÍÌÎÏĪÓÒÔÖÕŌÚÙÛÜŪÝŸÑÇ';
const A = 'aaaaaaaeeeeeiiiiioooooouuuuuyyncaaaaaaaeeeeeiiiiioooooouuuuuyync';
const MAPA = new Map([...DE].map((c, i) => [c, A[i]]));

/** «  ANA  García López » → «ana garcia lopez» */
function normalizarNombre(nombre) {
  return [...String(nombre || '').toLowerCase()]
    .map((c) => MAPA.get(c) || c)
    .join('')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Marca cada fila con:
 *   vigente      true si es la última respuesta de esa persona
 *   n_respuestas cuántas veces ha respondido esa persona (mismo nombre normalizado)
 * Devuelve las filas ordenadas de más reciente a más antigua.
 */
function marcarVigentes(filas) {
  const ordenadas = filas
    .map((f, i) => ({ f, i, t: Date.parse(f.created_at) || 0 }))
    .sort((a, b) => b.t - a.t || a.i - b.i) // empate: se respeta el orden de la API (id desc)
    .map((x) => x.f);
  const conteo = new Map();
  for (const f of ordenadas) {
    const k = normalizarNombre(f.nombre);
    conteo.set(k, (conteo.get(k) || 0) + 1);
  }
  const vistos = new Set();
  return ordenadas.map((f) => {
    const k = normalizarNombre(f.nombre);
    const vigente = !vistos.has(k);
    vistos.add(k);
    return { ...f, vigente, n_respuestas: conteo.get(k) };
  });
}

const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);

/** Totales (mismas columnas que la vista rsvp_resumen). */
function calcularResumen(filasMarcadas) {
  const vigentes = filasMarcadas.filter((f) => f.vigente);
  const si = vigentes.filter((f) => f.asistencia === 'si');
  const alergias = Object.fromEntries(OPCIONES_ALERGIA.map((o) => [o, 0]));
  let otras = 0;
  let conAlergias = 0;
  for (const f of si) {
    for (const a of Array.isArray(f.alergias) ? f.alergias : []) {
      conAlergias++;
      for (const o of Array.isArray(a.opciones) ? a.opciones : []) if (o in alergias) alergias[o]++;
      if (a.otras) otras++;
    }
  }
  return {
    respuestas_recibidas: filasMarcadas.length,
    respuestas_vigentes: vigentes.length,
    confirman_si: si.length,
    no_asisten: vigentes.length - si.length,
    personas_asisten: si.reduce((s, f) => s + 1 + num(f.n_acompanantes), 0),
    acompanantes: si.reduce((s, f) => s + num(f.n_acompanantes), 0),
    plazas_ida: si.reduce((s, f) => s + num(f.transporte_ida), 0),
    plazas_vuelta: si.reduce((s, f) => s + num(f.transporte_vuelta), 0),
    alergias,
    otras_alergias: otras,
    personas_con_alergias: conAlergias,
  };
}

module.exports = { normalizarNombre, marcarVigentes, calcularResumen };
