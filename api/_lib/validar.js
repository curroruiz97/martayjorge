'use strict';
/**
 * Validación y normalización de una confirmación de asistencia (RSVP).
 *
 * Es la ÚNICA fuente de verdad en el servidor: aunque el formulario ya valida,
 * aquí se vuelve a comprobar todo (tipos, rangos y longitudes), se recortan
 * espacios, se quitan caracteres de control/invisibles y se normaliza Unicode.
 * Los mensajes están en español y son los mismos que enseña el formulario.
 *
 * (Los ficheros de api/_lib/ no son funciones de Vercel: el guion bajo lo evita).
 */

const OPCIONES_ALERGIA = Object.freeze([
  'sin_gluten', 'sin_lactosa', 'vegetariano', 'vegano', 'frutos_secos', 'marisco',
]);

const LIMITES = Object.freeze({
  nombre: 120,          // nombre y apellidos (titular y acompañantes)
  nombreMin: 2,
  mensaje: 1000,        // «¿Algo que decirnos?»
  otras: 300,           // «Otras alergias o restricciones»
  acompanantes: 8,
  plazas: 9,            // plazas de autocar por trayecto (además, ≤ 1 + acompañantes)
  tiempoMinimoMs: 2500, // antibot: tiempo mínimo entre que se pinta el formulario y se envía
  cuerpoBytes: 20 * 1024,
  userAgent: 255,
});

const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RE_LETRA = /\p{L}/u;
// Invisibles que solo sirven para confundir: espacios de ancho cero, marcas e
// incrustaciones bidireccionales, BOM. (Se conservan U+200C/U+200D, que forman emojis).
const RE_INVISIBLES = /[\u200B\u200E\u200F\u202A-\u202E\u2060-\u2064\u2066-\u2069\uFEFF]/g;
// Mitades de emoji sueltas (sustitutos UTF-16 sin pareja): Postgres las rechazaría.
const RE_SUSTITUTOS_SUELTOS = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/g;

function normalizarBase(texto) {
  return texto.replace(RE_SUSTITUTOS_SUELTOS, '').normalize('NFC').replace(RE_INVISIBLES, '');
}

/** Texto de una línea: sin caracteres de control, espacios colapsados y recortado. */
function limpiarLinea(texto) {
  return normalizarBase(texto)
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Párrafo: conserva los saltos de línea (como mucho una línea en blanco seguida). */
function limpiarParrafo(texto) {
  return normalizarBase(texto)
    .replace(/\r\n?|[\u{2028}\u{2029}\u{85}]/gu, '\n')
    .replace(/[\u0000-\u0009\u000B-\u001F\u007F-\u009F]/g, ' ')
    .replace(/[^\S\n]+/g, ' ')
    .replace(/ ?\n ?/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

const esObjeto = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

function validarNombre(valor, campo, errores, mensajeVacio) {
  if (valor === undefined || valor === null) valor = '';
  if (typeof valor !== 'string') {
    errores[campo] = mensajeVacio;
    return '';
  }
  const limpio = limpiarLinea(valor);
  if (!limpio) errores[campo] = mensajeVacio;
  else if (limpio.length > LIMITES.nombre) errores[campo] = `Es demasiado largo (máximo ${LIMITES.nombre} caracteres).`;
  else if (limpio.length < LIMITES.nombreMin || !RE_LETRA.test(limpio)) errores[campo] = 'Escribe un nombre válido.';
  return limpio;
}

/**
 * Valida el JSON recibido. Devuelve
 *   { ok: true, datos }               datos listos para insertar en public.rsvps
 *   { ok: false, errores: {campo: mensaje} }
 * Claves de error: nombre, asistencia, acompanantes, acompanantes.N.nombre (N desde 0),
 * transporte, transporte.ida, transporte.vuelta, alergias, alergias.<persona>,
 * alergias.<persona>.otras, mensaje, submission_id, general.
 */
function validarRsvp(entrada) {
  if (!esObjeto(entrada)) {
    return { ok: false, errores: { general: 'Los datos enviados no son válidos.' } };
  }
  const errores = {};

  const submissionId = typeof entrada.submission_id === 'string' ? entrada.submission_id.trim().toLowerCase() : '';
  if (!RE_UUID.test(submissionId)) {
    errores.submission_id = 'Falta el identificador del envío. Recarga la página y vuelve a intentarlo.';
  }

  const nombre = validarNombre(entrada.nombre, 'nombre', errores, 'Escribe tu nombre y apellidos.');

  const asistencia = entrada.asistencia === 'si' || entrada.asistencia === 'no' ? entrada.asistencia : null;
  if (!asistencia) errores.asistencia = 'Indica si podrás asistir.';

  // Quien no asiste no trae acompañantes, autocar ni alergias: si llegan, se ignoran.
  let acompanantes = [];
  const transporte = { ida: 0, vuelta: 0 };
  let alergias = [];

  if (asistencia === 'si') {
    // --- Acompañantes ---
    const lista = entrada.acompanantes == null ? [] : entrada.acompanantes;
    if (!Array.isArray(lista)) {
      errores.acompanantes = 'La lista de acompañantes no es válida.';
    } else if (lista.length > LIMITES.acompanantes) {
      errores.acompanantes = `Puedes indicar como máximo ${LIMITES.acompanantes} acompañantes.`;
    } else {
      acompanantes = lista.map((a, i) => ({
        nombre: validarNombre(esObjeto(a) ? a.nombre : undefined, `acompanantes.${i}.nombre`, errores,
          `Escribe el nombre y apellidos del acompañante ${i + 1}.`),
      }));
    }

    // --- Autocar ---
    const maxPlazas = 1 + acompanantes.length;
    const t = entrada.transporte == null ? {} : entrada.transporte;
    if (!esObjeto(t)) {
      errores.transporte = 'Las plazas de autocar no son válidas.';
    } else {
      for (const tramo of ['ida', 'vuelta']) {
        const v = t[tramo] == null ? 0 : t[tramo];
        if (!Number.isInteger(v) || v < 0 || v > LIMITES.plazas) {
          errores[`transporte.${tramo}`] = `Indica un número de plazas entre 0 y ${LIMITES.plazas}.`;
        } else if (v > maxPlazas) {
          errores[`transporte.${tramo}`] = maxPlazas === 1
            ? 'Como máximo 1 plaza (la tuya).'
            : `Como máximo ${maxPlazas} plazas (tú y tus acompañantes).`;
        } else {
          transporte[tramo] = v;
        }
      }
    }

    // --- Alergias (solo personas con algo marcado o escrito) ---
    const personas = ['titular', ...acompanantes.map((_, i) => `acompanante_${i + 1}`)];
    const nombres = [nombre, ...acompanantes.map((a) => a.nombre)];
    const lista2 = entrada.alergias == null ? [] : entrada.alergias;
    if (!Array.isArray(lista2) || lista2.length > personas.length) {
      errores.alergias = 'Las alergias no son válidas.';
    } else {
      const porPersona = new Map();
      for (const item of lista2) {
        if (!esObjeto(item)) { errores.alergias = 'Las alergias no son válidas.'; break; }
        const idx = personas.indexOf(item.persona);
        if (idx === -1 || porPersona.has(item.persona)) {
          errores.alergias = 'Las alergias no corresponden a las personas del formulario.';
          break;
        }
        const ops = item.opciones == null ? [] : item.opciones;
        if (!Array.isArray(ops) || ops.length > 20 || !ops.every((o) => OPCIONES_ALERGIA.includes(o))) {
          errores[`alergias.${item.persona}`] = 'Alguna de las opciones marcadas no es válida.';
          continue;
        }
        let otras = '';
        if (item.otras != null) {
          if (typeof item.otras !== 'string') {
            errores[`alergias.${item.persona}.otras`] = 'Este texto no es válido.';
            continue;
          }
          otras = limpiarLinea(item.otras);
          if (otras.length > LIMITES.otras) {
            errores[`alergias.${item.persona}.otras`] = `Es demasiado largo (máximo ${LIMITES.otras} caracteres).`;
            continue;
          }
        }
        porPersona.set(item.persona, {
          persona: item.persona,
          nombre: nombres[idx],
          opciones: OPCIONES_ALERGIA.filter((o) => ops.includes(o)), // sin repetidos y en orden fijo
          otras,
        });
      }
      alergias = personas
        .filter((p) => porPersona.has(p))
        .map((p) => porPersona.get(p))
        .filter((a) => a.opciones.length > 0 || a.otras !== '');
    }
  }

  // --- Mensaje ---
  let mensaje = '';
  if (entrada.mensaje != null) {
    if (typeof entrada.mensaje !== 'string') {
      errores.mensaje = 'El mensaje no es válido.';
    } else {
      mensaje = limpiarParrafo(entrada.mensaje);
      if (mensaje.length > LIMITES.mensaje) {
        errores.mensaje = `El mensaje es demasiado largo (máximo ${LIMITES.mensaje} caracteres).`;
      }
    }
  }

  if (Object.keys(errores).length) return { ok: false, errores };

  return {
    ok: true,
    datos: {
      submission_id: submissionId,
      nombre,
      asistencia,
      n_acompanantes: acompanantes.length,
      acompanantes,
      transporte_ida: transporte.ida,
      transporte_vuelta: transporte.vuelta,
      alergias,
      mensaje,
    },
  };
}

/** User-Agent recortado y sin caracteres raros (solo para diagnosticar problemas). */
function recortarUserAgent(valor) {
  if (typeof valor !== 'string') return null;
  const limpio = limpiarLinea(valor).slice(0, LIMITES.userAgent).replace(RE_SUSTITUTOS_SUELTOS, '');
  return limpio || null;
}

module.exports = {
  OPCIONES_ALERGIA,
  LIMITES,
  validarRsvp,
  limpiarLinea,
  limpiarParrafo,
  recortarUserAgent,
};
