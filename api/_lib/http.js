'use strict';
/**
 * Utilidades HTTP sin dependencias. Solo usan la API estándar de Node
 * (res.statusCode / res.setHeader / res.end), así que funcionan igual en Vercel
 * (con o sin sus «helpers») y en el servidor de desarrollo (scripts/dev.mjs).
 */

function enviarJSON(res, status, datos, cabeceras = {}) {
  if (res.writableEnded) return;
  const cuerpo = JSON.stringify(datos);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Robots-Tag', 'noindex');
  for (const [clave, valor] of Object.entries(cabeceras)) res.setHeader(clave, valor);
  res.setHeader('Content-Length', Buffer.byteLength(cuerpo));
  res.end(cuerpo);
}

/** ¿La petición dice que trae JSON? (admite «application/json; charset=utf-8») */
function esJSON(req) {
  const tipo = String(req.headers['content-type'] || '').split(';')[0].trim().toLowerCase();
  return tipo === 'application/json';
}

/**
 * Lee y parsea el cuerpo JSON con un límite de tamaño.
 * Devuelve { ok: true, valor } o { ok: false, status, error }.
 *
 * En Vercel, sus «helpers» pueden haber leído ya el flujo y dejar el resultado
 * en req.body (un getter que lanza si el JSON está mal): se usa ese valor.
 * En Node puro se lee el flujo directamente.
 */
async function leerCuerpoJSON(req, limite) {
  const declarado = Number(req.headers['content-length']);
  if (Number.isFinite(declarado) && declarado > limite) {
    return { ok: false, status: 413, error: 'La petición es demasiado grande.' };
  }

  const yaLeido = Object.prototype.hasOwnProperty.call(req, 'body') || req.readableEnded === true;
  if (yaLeido) {
    let cuerpo;
    try {
      cuerpo = req.body;
    } catch {
      return { ok: false, status: 400, error: 'El JSON no es válido.' };
    }
    if (cuerpo === undefined || cuerpo === null || cuerpo === '') {
      return { ok: false, status: 400, error: 'Falta el cuerpo de la petición.' };
    }
    if (Buffer.isBuffer(cuerpo)) cuerpo = cuerpo.toString('utf8');
    if (typeof cuerpo === 'string') {
      if (Buffer.byteLength(cuerpo) > limite) return { ok: false, status: 413, error: 'La petición es demasiado grande.' };
      return parsear(cuerpo);
    }
    if (typeof cuerpo === 'object') {
      if (Buffer.byteLength(JSON.stringify(cuerpo)) > limite) {
        return { ok: false, status: 413, error: 'La petición es demasiado grande.' };
      }
      return { ok: true, valor: cuerpo };
    }
    return { ok: false, status: 400, error: 'El JSON no es válido.' };
  }

  const leido = await leerFlujo(req, limite);
  if (leido.excedido) return { ok: false, status: 413, error: 'La petición es demasiado grande.' };
  if (leido.error) return { ok: false, status: 400, error: 'No se pudo leer la petición.' };
  if (!leido.buffer.length) return { ok: false, status: 400, error: 'Falta el cuerpo de la petición.' };
  return parsear(leido.buffer.toString('utf8'));
}

function parsear(texto) {
  try {
    return { ok: true, valor: JSON.parse(texto) };
  } catch {
    return { ok: false, status: 400, error: 'El JSON no es válido.' };
  }
}

function leerFlujo(req, limite) {
  return new Promise((resolve) => {
    const trozos = [];
    let total = 0;
    let terminado = false;
    const acabar = (resultado) => {
      if (terminado) return;
      terminado = true;
      resolve(resultado);
    };
    req.on('data', (trozo) => {
      if (terminado) return; // si se pasó del límite, el resto se descarta
      total += trozo.length;
      if (total > limite) {
        trozos.length = 0;
        acabar({ excedido: true });
        return;
      }
      trozos.push(trozo);
    });
    req.on('end', () => acabar({ buffer: Buffer.concat(trozos) }));
    req.on('error', () => acabar({ error: true }));
    req.on('aborted', () => acabar({ error: true }));
  });
}

const pausa = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Token de «Authorization: Bearer …». El panel lo envía con encodeURIComponent
 * para admitir contraseñas con tildes o ñ (las cabeceras HTTP solo admiten ASCII).
 */
function leerBearer(req) {
  const m = /^Bearer\s+(.+)$/i.exec(String(req.headers.authorization || ''));
  if (!m) return '';
  const valor = m[1].trim();
  try {
    return decodeURIComponent(valor);
  } catch {
    return valor;
  }
}

/** Comparación en tiempo constante (no revela por el tiempo cuántos caracteres coinciden). */
function mismoSecreto(a, b) {
  const crypto = require('node:crypto');
  const ha = crypto.createHash('sha256').update(String(a), 'utf8').digest();
  const hb = crypto.createHash('sha256').update(String(b), 'utf8').digest();
  return crypto.timingSafeEqual(ha, hb);
}

module.exports = { enviarJSON, esJSON, leerCuerpoJSON, pausa, leerBearer, mismoSecreto };
