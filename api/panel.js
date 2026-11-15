'use strict';
/**
 * /api/panel — panel de los novios (/panel), con usuario y contraseña de Supabase Auth.
 *
 *   POST /api/panel?accion=entrar   { email, password }  → { ok, sesion, usuario }
 *   POST /api/panel?accion=renovar  { refresh_token }    → { ok, sesion, usuario }
 *   POST /api/panel?accion=salir    (Authorization: Bearer <access_token>) → { ok }
 *   GET  /api/panel                 (Authorization: Bearer <access_token>)
 *        → { ok, usuario, generado, resumen, respuestas, limite_alcanzado }
 *
 * Seguridad:
 *   · Las cuentas se crean a mano en Supabase → Authentication → Users (no hay registro en la web).
 *   · Además, el correo tiene que estar en public.panel_acceso: una cuenta que no esté ahí no ve nada.
 *   · El navegador nunca habla con Supabase ni ve la clave secreta: todo pasa por aquí.
 *   · Contraseña mal → espera ~0,8 s y 401 (sin decir si el correo existe).
 */

const { enviarJSON, esJSON, leerCuerpoJSON, pausa, leerBearer } = require('./_lib/http');
const {
  leerConfig, listarRsvps, describirError, ErrorSupabase,
  entrarConContrasena, renovarSesion, usuarioDeToken, cerrarSesion, accesoPanel,
} = require('./_lib/supabase');
const { marcarVigentes, calcularResumen } = require('./_lib/resumen');

const CABECERAS = {
  'Cache-Control': 'no-store, private',
  'X-Robots-Tag': 'noindex, nofollow',
  'Referrer-Policy': 'no-referrer',
  Vary: 'Authorization',
};
const LIMITE_CUERPO = 4 * 1024;
const RE_EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;
const SIN_ACCESO = 'Esta cuenta no tiene acceso al panel. Pide que añadan tu correo a la lista de acceso.';

const responder = (res, status, datos, extra = {}) => enviarJSON(res, status, datos, { ...CABECERAS, ...extra });
const esperaAleatoria = () => pausa(600 + Math.floor(Math.random() * 400)); // frena los intentos a ciegas

function publicoDeSesion(s, acceso) {
  return {
    sesion: { access_token: s.access_token, refresh_token: s.refresh_token, expires_at: s.expires_at },
    usuario: { email: acceso.email, nombre: acceso.nombre },
  };
}

async function entrar(req, res, cfg) {
  const cuerpo = await leerCuerpoJSON(req, LIMITE_CUERPO);
  if (!cuerpo.ok) return responder(res, cuerpo.status, { ok: false, error: cuerpo.error });
  const v = cuerpo.valor || {};
  const email = String(v.email || '').trim().toLowerCase();
  const password = typeof v.password === 'string' ? v.password : '';
  if (!RE_EMAIL.test(email) || password.length < 6 || password.length > 200) {
    await esperaAleatoria();
    return responder(res, 401, { ok: false, error: 'Correo o contraseña incorrectos.' });
  }
  const sesion = await entrarConContrasena(cfg, email, password);
  if (!sesion) {
    await esperaAleatoria();
    return responder(res, 401, { ok: false, error: 'Correo o contraseña incorrectos.' });
  }
  const acceso = await accesoPanel(cfg, sesion.email || email);
  if (!acceso) {
    await cerrarSesion(cfg, sesion.access_token);
    return responder(res, 403, { ok: false, error: SIN_ACCESO });
  }
  return responder(res, 200, { ok: true, ...publicoDeSesion(sesion, acceso) });
}

async function renovar(req, res, cfg) {
  const cuerpo = await leerCuerpoJSON(req, LIMITE_CUERPO);
  if (!cuerpo.ok) return responder(res, cuerpo.status, { ok: false, error: cuerpo.error });
  const refresh = String((cuerpo.valor || {}).refresh_token || '');
  const sesion = refresh && refresh.length <= 2000 ? await renovarSesion(cfg, refresh) : null;
  if (!sesion) return responder(res, 401, { ok: false, error: 'La sesión ha caducado. Vuelve a entrar.' });
  const acceso = await accesoPanel(cfg, sesion.email);
  if (!acceso) {
    await cerrarSesion(cfg, sesion.access_token);
    return responder(res, 403, { ok: false, error: SIN_ACCESO });
  }
  return responder(res, 200, { ok: true, ...publicoDeSesion(sesion, acceso) });
}

async function salir(req, res, cfg) {
  const token = leerBearer(req);
  if (token && token.length <= 4000) await cerrarSesion(cfg, token);
  return responder(res, 200, { ok: true });
}

async function datos(req, res, cfg) {
  const token = leerBearer(req);
  const usuario = token && token.length <= 4000 ? await usuarioDeToken(cfg, token) : null;
  if (!usuario) return responder(res, 401, { ok: false, error: 'La sesión ha caducado. Vuelve a entrar.' }, { 'WWW-Authenticate': 'Bearer' });
  const acceso = await accesoPanel(cfg, usuario.email);
  if (!acceso) return responder(res, 403, { ok: false, error: SIN_ACCESO });

  const { filas, limiteAlcanzado } = await listarRsvps(cfg);
  const respuestas = marcarVigentes(filas);
  return responder(res, 200, {
    ok: true,
    usuario: { email: acceso.email, nombre: acceso.nombre },
    generado: new Date().toISOString(),
    resumen: calcularResumen(respuestas),
    respuestas,
    limite_alcanzado: limiteAlcanzado,
  });
}

module.exports = async function panel(req, res) {
  try {
    const cfg = leerConfig();
    if (!cfg.ok) {
      console.error('[panel] Configuración incompleta:', cfg.motivo);
      return responder(res, 503, { ok: false, error: cfg.motivo });
    }
    const accion = new URL(req.url || '/', 'http://localhost').searchParams.get('accion') || '';

    if (req.method === 'GET' && !accion) return await datos(req, res, cfg);
    if (req.method === 'POST' && ['entrar', 'renovar', 'salir'].includes(accion)) {
      if (accion !== 'salir' && !esJSON(req)) return responder(res, 415, { ok: false, error: 'Se esperaba JSON.' });
      if (accion === 'entrar') return await entrar(req, res, cfg);
      if (accion === 'renovar') return await renovar(req, res, cfg);
      return await salir(req, res, cfg);
    }
    return responder(res, 405, { ok: false, error: 'Método no permitido.' }, { Allow: 'GET, POST' });
  } catch (err) {
    console.error('[panel]', describirError(err));
    const error = err instanceof ErrorSupabase ? err.diagnostico : 'Ha ocurrido un error inesperado.';
    return responder(res, err instanceof ErrorSupabase && err.status === 429 ? 429 : 503, { ok: false, error });
  }
};
