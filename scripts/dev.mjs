#!/usr/bin/env node
/**
 * Servidor de desarrollo de la web de Marta y Jorge (sin dependencias).
 *
 *   npm run dev                  → MOCK_SUPABASE=1: base de datos simulada (no hace falta Supabase)
 *   node scripts/dev.mjs         → usa el Supabase real de las variables de .env
 *
 * Qué hace:
 *   · Sirve public/ con URLs limpias como Vercel (/admin → /admin/index.html).
 *   · Monta api/*.js como funciones de Vercel (se recargan solas al editarlas).
 *   · Aplica las cabeceras de vercel.json (incluida la CSP) para ver los fallos antes de desplegar.
 *   · MOCK_SUPABASE=1: imita la API de Supabase (PostgREST) con las mismas columnas y
 *     restricciones que supabase/schema.sql; guarda en memoria y en .dev-data/rsvps.json.
 *   · /_dev/rsvp   → el formulario aislado (vista previa de public/partials/rsvp.html).
 *     /_dev/pagina → index.html con el formulario ya insertado entre <!-- RSVP:INICIO/FIN -->.
 *
 * Variables: PORT (3000), HOST (127.0.0.1), MOCK_SUPABASE, DEV_DATA_DIR, ADMIN_TOKEN.
 */

import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PUBLICO = path.join(RAIZ, 'public');
const DIR_API = path.join(RAIZ, 'api');
const requerir = createRequire(import.meta.url);

const CLAVE_MOCK = 'sb_secret_mock_desarrollo_local';
const TOKEN_ADMIN_DEV = 'desarrollo-local-2027';

const TIPOS = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.avif': 'image/avif', '.gif': 'image/gif', '.ico': 'image/x-icon',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.xml': 'application/xml',
  '.webmanifest': 'application/manifest+json', '.pdf': 'application/pdf', '.mp4': 'video/mp4',
};

/* ------------------------------------------------------------------ utilidades */

function cargarEnv(fichero) {
  let texto;
  try { texto = fs.readFileSync(fichero, 'utf8'); } catch { return 0; }
  let n = 0;
  for (const linea of texto.split(/\r?\n/)) {
    if (/^\s*(#|$)/.test(linea)) continue;
    const m = /^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/.exec(linea);
    if (!m) continue;
    let valor = m[2];
    if (/^(["']).*\1$/.test(valor)) valor = valor.slice(1, -1);
    else valor = valor.replace(/\s+#.*$/, '');
    if (process.env[m[1]] === undefined) { process.env[m[1]] = valor; n++; }
  }
  return n;
}

function leerVercelJson() {
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(RAIZ, 'vercel.json'), 'utf8'));
    const reglas = [];
    for (const r of Array.isArray(cfg.headers) ? cfg.headers : []) {
      try { reglas.push({ re: new RegExp(`^${r.source}$`), headers: r.headers || [] }); } catch { /* patrón no soportado */ }
    }
    return { cleanUrls: cfg.cleanUrls !== false, reglas };
  } catch {
    return { cleanUrls: true, reglas: [] };
  }
}

function aplicarCabecerasVercel(res, pathname, vercel) {
  for (const regla of vercel.reglas) {
    if (!regla.re.test(pathname)) continue;
    for (const h of regla.headers) if (h && h.key) res.setHeader(h.key, h.value);
  }
}

function json(res, status, datos) {
  const cuerpo = JSON.stringify(datos);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(cuerpo);
}

async function existeFichero(p) {
  try { return (await fsp.stat(p)).isFile(); } catch { return false; }
}

function leerCuerpo(req, limite = 5 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const trozos = [];
    let total = 0;
    req.on('data', (t) => { total += t.length; if (total <= limite) trozos.push(t); });
    req.on('end', () => resolve(total > limite ? null : Buffer.concat(trozos).toString('utf8')));
    req.on('error', reject);
  });
}

/* ----------------------------------------------------- Supabase simulado (mock) */

const COLUMNAS = ['id', 'created_at', 'submission_id', 'nombre', 'asistencia', 'n_acompanantes', 'acompanantes',
  'transporte_ida', 'transporte_vuelta', 'alergias', 'mensaje', 'user_agent'];
const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const largo = (s) => [...s].length; // como char_length de Postgres (puntos de código)
const entero = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;

/** Comprueba tipos y restricciones igual que supabase/schema.sql. Devuelve un error PostgREST o null. */
function comprobarFila(f) {
  for (const k of Object.keys(f)) {
    if (!COLUMNAS.includes(k)) return { status: 400, code: 'PGRST204', message: `Could not find the '${k}' column of 'rsvps' in the schema cache` };
  }
  if (typeof f.submission_id !== 'string' || !RE_UUID.test(f.submission_id)) return { status: 400, code: '22P02', message: 'invalid input syntax for type uuid' };
  for (const k of ['nombre', 'asistencia']) {
    if (f[k] === undefined || f[k] === null) return { status: 400, code: '23502', message: `null value in column "${k}" of relation "rsvps" violates not-null constraint` };
    if (typeof f[k] !== 'string') return { status: 400, code: '22P02', message: `invalid input for column "${k}"` };
  }
  for (const k of ['n_acompanantes', 'transporte_ida', 'transporte_vuelta']) {
    if (!Number.isInteger(f[k])) return { status: 400, code: '22P02', message: `invalid input syntax for type smallint (${k})` };
  }
  if (typeof f.mensaje !== 'string') return { status: 400, code: '22P02', message: 'invalid input for column "mensaje"' };
  if (f.user_agent !== null && typeof f.user_agent !== 'string') return { status: 400, code: '22P02', message: 'invalid input for column "user_agent"' };
  const viola = (nombre) => ({ status: 400, code: '23514', message: `new row for relation "rsvps" violates check constraint "${nombre}"` });
  const n = f.n_acompanantes;
  if (!(largo(f.nombre.trim()) >= 1 && largo(f.nombre.trim()) <= 120)) return viola('rsvps_nombre_chk');
  if (!['si', 'no'].includes(f.asistencia)) return viola('rsvps_asistencia_chk');
  if (!entero(n, 0, 8)) return viola('rsvps_n_acompanantes_chk');
  if (!Array.isArray(f.acompanantes) || f.acompanantes.length !== n) return viola('rsvps_acompanantes_chk');
  if (!entero(f.transporte_ida, 0, 9) || !entero(f.transporte_vuelta, 0, 9) || f.transporte_ida > n + 1 || f.transporte_vuelta > n + 1) return viola('rsvps_transporte_chk');
  if (!Array.isArray(f.alergias) || f.alergias.length > n + 1) return viola('rsvps_alergias_chk');
  if (largo(f.mensaje) > 1000) return viola('rsvps_mensaje_chk');
  if (f.user_agent !== null && largo(f.user_agent) > 300) return viola('rsvps_user_agent_chk');
  if (f.asistencia === 'no' && (n !== 0 || f.transporte_ida !== 0 || f.transporte_vuelta !== 0 || f.alergias.length !== 0)) return viola('rsvps_no_asiste_chk');
  return null;
}

function crearMock(dirDatos) {
  const fichero = path.join(dirDatos, 'rsvps.json');
  let filas = [];
  try {
    const previo = JSON.parse(fs.readFileSync(fichero, 'utf8'));
    if (Array.isArray(previo)) filas = previo;
  } catch { /* primera vez */ }
  let ultimoInstante = 0;
  let cola = Promise.resolve();

  const guardar = () => {
    cola = cola.then(async () => {
      await fsp.mkdir(dirDatos, { recursive: true });
      const tmp = `${fichero}.${process.pid}.tmp`;
      await fsp.writeFile(tmp, JSON.stringify(filas, null, 2) + '\n', 'utf8');
      await fsp.rename(tmp, fichero); // escritura atómica
    });
    return cola;
  };

  const proyectar = (fila, select) => {
    if (!select || select === '*') return { ...fila };
    const out = {};
    for (const c of select.split(',').map((s) => s.trim()).filter(Boolean)) if (c in fila) out[c] = fila[c];
    return out;
  };

  async function manejar(req, res, url) {
    if (req.headers.apikey !== CLAVE_MOCK) {
      return json(res, 401, { message: 'Invalid API key', hint: 'Double check your Supabase `anon` or `service_role` API key.' });
    }
    // Igual que Supabase: una clave sb_secret_ no es un JWT y no puede ir en Authorization.
    if (req.headers.authorization && !/^Bearer eyJ/.test(req.headers.authorization)) {
      return json(res, 401, { code: 'PGRST301', message: 'Invalid JWT' });
    }
    const ruta = url.pathname.replace(/^\/__supabase/, '');
    if (ruta !== '/rest/v1/rsvps') {
      return json(res, 404, { code: 'PGRST205', message: `Could not find the table '${ruta.replace('/rest/v1/', 'public.')}' in the schema cache` });
    }
    const select = url.searchParams.get('select');

    if (req.method === 'GET') {
      let lista = [...filas];
      const orden = url.searchParams.get('order');
      if (orden) {
        const criterios = orden.split(',').map((c) => c.split('.'));
        lista.sort((a, b) => {
          for (const [col, dir] of criterios) {
            const va = a[col]; const vb = b[col];
            if (va === vb) continue;
            const cmp = va < vb ? -1 : 1;
            return dir === 'desc' ? -cmp : cmp;
          }
          return 0;
        });
      }
      const limite = Number(url.searchParams.get('limit'));
      if (Number.isInteger(limite) && limite >= 0) lista = lista.slice(0, limite);
      return json(res, 200, lista.map((f) => proyectar(f, select)));
    }

    if (req.method === 'POST') {
      const texto = await leerCuerpo(req);
      let entrada;
      try { entrada = JSON.parse(texto); } catch { return json(res, 400, { code: 'PGRST102', message: 'Empty or invalid json' }); }
      const prefer = String(req.headers.prefer || '');
      const ignorarDuplicados = url.searchParams.get('on_conflict') === 'submission_id' && /resolution=ignore-duplicates/.test(prefer);
      const nuevas = [];
      for (const obj of Array.isArray(entrada) ? entrada : [entrada]) {
        const instante = Math.max(Date.now(), ultimoInstante + 1);
        ultimoInstante = instante;
        const fila = {
          id: crypto.randomUUID(), created_at: new Date(instante).toISOString(),
          n_acompanantes: 0, acompanantes: [], transporte_ida: 0, transporte_vuelta: 0,
          alergias: [], mensaje: '', user_agent: null, ...obj,
        };
        const fallo = comprobarFila(fila);
        if (fallo) return json(res, fallo.status, { code: fallo.code, message: fallo.message, details: null, hint: null });
        const repetida = filas.some((f) => f.submission_id === fila.submission_id) || nuevas.some((f) => f.submission_id === fila.submission_id);
        if (repetida) {
          if (ignorarDuplicados) continue;
          return json(res, 409, { code: '23505', message: 'duplicate key value violates unique constraint "rsvps_submission_id_key"' });
        }
        nuevas.push(fila);
      }
      filas.push(...nuevas);
      if (nuevas.length) await guardar();
      res.statusCode = 201;
      if (/return=representation/.test(prefer)) {
        return json(res, 201, nuevas.map((f) => proyectar(f, select)));
      }
      return res.end();
    }
    return json(res, 405, { message: 'Method not allowed' });
  }

  return {
    manejar,
    fichero,
    filas: () => filas.map((f) => ({ ...f })),
    vaciar: async () => { filas = []; await guardar(); },
  };
}

/* ------------------------------------------------------------ vistas previas */

async function vistaPreviaFormulario() {
  const parcial = await fsp.readFile(path.join(PUBLICO, 'partials', 'rsvp.html'), 'utf8');
  const hay = async (rel) => existeFichero(path.join(PUBLICO, rel));
  return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <link rel="icon" href="data:,">
  <title>Vista previa · Confirmación</title>
  ${(await hay('js/boot.js')) ? '<script src="/js/boot.js"></script>' : ''}
  <link rel="stylesheet" href="/css/base.css">
  ${(await hay('css/site.css')) ? '<link rel="stylesheet" href="/css/site.css">' : ''}
  <link rel="stylesheet" href="/css/rsvp.css">
</head>
<body>
<main>
${parcial}
</main>
<div class="aviso" id="aviso" role="status" aria-live="polite" hidden></div>
${(await hay('js/main.js')) ? '<script src="/js/main.js" defer></script>' : ''}
<script src="/js/rsvp.js" defer></script>
</body>
</html>
`;
}

async function paginaConFormulario() {
  const indice = await fsp.readFile(path.join(PUBLICO, 'index.html'), 'utf8');
  const parcial = await fsp.readFile(path.join(PUBLICO, 'partials', 'rsvp.html'), 'utf8');
  const ini = indice.indexOf('<!-- RSVP:INICIO');
  const fin = indice.indexOf('<!-- RSVP:FIN');
  if (ini === -1 || fin === -1 || fin < ini) return null;
  const finIni = indice.indexOf('-->', ini) + 3;
  return (indice.slice(0, finIni) + '\n' + parcial + '\n  ' + indice.slice(fin))
    .replace('<head>', '<head>\n  <base href="/">');
}

/* ------------------------------------------------------------------ servidor */

export async function iniciar({
  puerto = Number(process.env.PORT) || 3000,
  host = process.env.HOST || '127.0.0.1',
  mock = /^(1|true|si|sí)$/i.test(process.env.MOCK_SUPABASE || ''),
  dirDatos = process.env.DEV_DATA_DIR || path.join(RAIZ, '.dev-data'),
  silencioso = false,
} = {}) {
  const log = silencioso ? () => {} : (...a) => console.log(...a);
  if (!mock) cargarEnv(path.join(RAIZ, '.env'));
  const supabaseMock = mock ? crearMock(dirDatos) : null;

  const servidor = http.createServer(async (req, res) => {
    const inicio = Date.now();
    let url;
    try {
      url = new URL(req.url, 'http://localhost');
    } catch {
      res.statusCode = 400;
      return res.end('Petición no válida');
    }
    const pathname = url.pathname;
    const vercel = leerVercelJson();
    res.on('finish', () => {
      if (!pathname.startsWith('/__supabase')) log(`[dev] ${res.statusCode} ${req.method} ${pathname} ${Date.now() - inicio}ms`);
    });

    try {
      // Supabase simulado
      if (pathname.startsWith('/__supabase/')) {
        if (!supabaseMock) return json(res, 404, { message: 'Mock desactivado (usa MOCK_SUPABASE=1)' });
        return await supabaseMock.manejar(req, res, url);
      }

      aplicarCabecerasVercel(res, pathname, vercel);

      // Funciones (api/*.js)
      if (pathname === '/api' || pathname.startsWith('/api/')) {
        const nombre = pathname.slice(5).replace(/\/+$/, '');
        const valido = /^[a-z0-9][a-z0-9-]*(\/[a-z0-9][a-z0-9-]*)*$/i.test(nombre);
        const fichero = valido ? path.join(DIR_API, `${nombre}.js`) : '';
        if (!fichero || !(await existeFichero(fichero))) return json(res, 404, { ok: false, error: 'No encontrado.' });
        for (const k of Object.keys(requerir.cache)) if (k.startsWith(DIR_API + path.sep)) delete requerir.cache[k];
        const modulo = requerir(fichero);
        const manejador = typeof modulo === 'function' ? modulo : modulo && modulo.default;
        if (typeof manejador !== 'function') return json(res, 500, { ok: false, error: `${nombre}.js no exporta una función` });
        await manejador(req, res);
        return;
      }

      // Vistas previas de desarrollo
      if (pathname === '/_dev/rsvp' || pathname === '/_dev/pagina') {
        const html = pathname === '/_dev/rsvp' ? await vistaPreviaFormulario() : await paginaConFormulario();
        if (html === null) { res.statusCode = 404; return res.end('index.html no tiene los marcadores <!-- RSVP:INICIO --> / <!-- RSVP:FIN -->'); }
        res.statusCode = 200;
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.setHeader('Cache-Control', 'no-store');
        return res.end(html);
      }

      // Ficheros estáticos
      if (req.method !== 'GET' && req.method !== 'HEAD') {
        res.statusCode = 405;
        res.setHeader('Allow', 'GET, HEAD');
        return res.end('Método no permitido');
      }
      let relativo;
      try { relativo = decodeURIComponent(pathname); } catch { res.statusCode = 400; return res.end('Ruta no válida'); }
      const abs = path.resolve(PUBLICO, '.' + relativo);
      if (relativo.includes('\0') || (abs !== PUBLICO && !abs.startsWith(PUBLICO + path.sep))) {
        res.statusCode = 404;
        return res.end('No encontrado');
      }
      const candidatos = [abs, path.join(abs, 'index.html')];
      if (vercel.cleanUrls && !path.extname(abs)) candidatos.push(`${abs}.html`);
      let elegido = null;
      for (const c of candidatos) if (await existeFichero(c)) { elegido = c; break; }
      if (!elegido) {
        const pagina404 = path.join(PUBLICO, '404.html');
        res.statusCode = 404;
        if (await existeFichero(pagina404)) {
          res.setHeader('Content-Type', TIPOS['.html']);
          return res.end(await fsp.readFile(pagina404));
        }
        res.setHeader('Content-Type', 'text/plain; charset=utf-8');
        return res.end('No encontrado');
      }
      const contenido = await fsp.readFile(elegido);
      res.statusCode = 200;
      res.setHeader('Content-Type', TIPOS[path.extname(elegido).toLowerCase()] || 'application/octet-stream');
      res.setHeader('Content-Length', contenido.length);
      res.setHeader('Cache-Control', 'no-store'); // en desarrollo, siempre fresco
      return res.end(req.method === 'HEAD' ? undefined : contenido);
    } catch (err) {
      console.error('[dev] Error atendiendo', req.method, pathname, '\n', err);
      if (!res.headersSent) return json(res, 500, { ok: false, error: 'Error interno del servidor de desarrollo.' });
      res.end();
    }
  });

  await new Promise((resolve, reject) => {
    servidor.once('error', reject);
    servidor.listen(puerto, host, resolve);
  });
  const direccion = servidor.address();
  const url = `http://${host === '0.0.0.0' ? '127.0.0.1' : host}:${direccion.port}`;

  if (mock) {
    // En modo simulado NUNCA se habla con un Supabase real.
    process.env.SUPABASE_URL = `${url}/__supabase`;
    process.env.SUPABASE_SECRET_KEY = CLAVE_MOCK;
    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    if (!process.env.ADMIN_TOKEN) process.env.ADMIN_TOKEN = TOKEN_ADMIN_DEV;
  }

  log(`\n  Marta y Jorge · servidor de desarrollo → ${url}`);
  log(`  Formulario aislado: ${url}/_dev/rsvp · página completa con formulario: ${url}/_dev/pagina`);
  if (mock) {
    log(`  Supabase SIMULADO: los envíos se guardan en ${path.relative(RAIZ, supabaseMock.fichero) || supabaseMock.fichero}`);
    log(`  Panel: ${url}/admin  (contraseña: ${process.env.ADMIN_TOKEN === TOKEN_ADMIN_DEV ? TOKEN_ADMIN_DEV : 'la de ADMIN_TOKEN'})\n`);
  } else if (!process.env.SUPABASE_URL) {
    log('  Aviso: sin MOCK_SUPABASE ni SUPABASE_URL, /api/rsvp responderá 503. Usa «npm run dev» o crea .env (ver .env.example).\n');
  } else {
    log('  Usando el Supabase REAL de .env: ¡ojo, los envíos de prueba se guardan de verdad!\n');
  }

  return {
    servidor,
    url,
    mock: supabaseMock,
    cerrar: () => new Promise((resolve) => {
      servidor.closeAllConnections?.();
      servidor.close(() => resolve());
    }),
  };
}

// Ejecutado directamente (no importado desde los tests)
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) {
  iniciar().catch((err) => {
    if (err && err.code === 'EADDRINUSE') {
      console.error(`El puerto ya está en uso. Prueba con otro: PORT=3001 npm run dev`);
    } else {
      console.error(err);
    }
    process.exit(1);
  });
}
