/**
 * Pruebas del flujo de confirmación (API + Supabase simulado).
 *   node --test scripts/test-rsvp.mjs        (o «npm test»)
 * No necesita Supabase real ni conexión: arranca scripts/dev.mjs en modo simulado
 * en un puerto libre y con una carpeta de datos temporal.
 */

import test, { before, after, describe } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import os from 'node:os';
import fs from 'node:fs/promises';
import path from 'node:path';
import { Readable } from 'node:stream';
import { createRequire } from 'node:module';
import { randomUUID } from 'node:crypto';
import { iniciar } from './dev.mjs';

const requerir = createRequire(import.meta.url);
const manejadorRsvp = requerir('../api/rsvp.js');
const { normalizarNombre, marcarVigentes, calcularResumen } = requerir('../api/_lib/resumen.js');
const { limpiarLinea } = requerir('../api/_lib/validar.js');

let srv;
let dirDatos;

before(async () => {
  dirDatos = await fs.mkdtemp(path.join(os.tmpdir(), 'mj-rsvp-test-'));
  delete process.env.ADMIN_TOKEN;
  delete process.env.CRON_SECRET;
  srv = await iniciar({ puerto: 0, mock: true, dirDatos, silencioso: true });
});

after(async () => {
  await srv.cerrar();
  await fs.rm(dirDatos, { recursive: true, force: true });
});

/* ------------------------------------------------------------ utilidades */

function valido(extra = {}) {
  return {
    submission_id: randomUUID(),
    nombre: 'Ana García López',
    asistencia: 'si',
    acompanantes: [{ nombre: 'Luis Pérez Gil' }, { nombre: 'Nuria Peña' }],
    transporte: { ida: 3, vuelta: 2 },
    alergias: [
      { persona: 'titular', opciones: ['sin_gluten', 'vegano'], otras: '' },
      { persona: 'acompanante_2', opciones: [], otras: 'Alergia al huevo' },
    ],
    mensaje: '¡Qué ganas de veros!',
    web: '',
    t: 8000,
    ...extra,
  };
}

async function enviar(cuerpo, { metodo = 'POST', tipo = 'application/json', ruta = '/api/rsvp', cabeceras = {} } = {}) {
  const r = await fetch(srv.url + ruta, {
    method: metodo,
    headers: { ...(tipo ? { 'Content-Type': tipo } : {}), ...cabeceras },
    body: metodo === 'GET' || metodo === 'HEAD' ? undefined : (typeof cuerpo === 'string' ? cuerpo : JSON.stringify(cuerpo)),
  });
  const texto = await r.text();
  let json = null;
  try { json = JSON.parse(texto); } catch { /* no es JSON */ }
  return { status: r.status, json, texto, headers: r.headers };
}

const filas = () => srv.mock.filas();
const buscar = (submissionId) => filas().find((f) => f.submission_id === submissionId);

async function conEntorno(cambios, fn) {
  const previo = {};
  for (const [k, v] of Object.entries(cambios)) {
    previo[k] = process.env[k];
    if (v === undefined) delete process.env[k]; else process.env[k] = v;
  }
  try {
    return await fn();
  } finally {
    for (const [k, v] of Object.entries(previo)) {
      if (v === undefined) delete process.env[k]; else process.env[k] = v;
    }
  }
}

/** req/res falsos para llamar al manejador como lo haría Vercel con sus «helpers». */
function reqVercel({ body, cuerpoLanza = false, headers = {} }) {
  const req = Readable.from([]);
  req.resume(); // flujo ya consumido, como cuando Vercel ha leído el cuerpo
  req.method = 'POST';
  req.headers = { 'content-type': 'application/json', ...headers };
  Object.defineProperty(req, 'body', {
    enumerable: true,
    get() {
      if (cuerpoLanza) throw new Error('Invalid JSON');
      return body;
    },
  });
  return req;
}

function resFalso() {
  const cabeceras = {};
  let resolver;
  const fin = new Promise((r) => { resolver = r; });
  return {
    statusCode: 200,
    writableEnded: false,
    setHeader(k, v) { cabeceras[k.toLowerCase()] = v; },
    getHeader(k) { return cabeceras[k.toLowerCase()]; },
    end(cuerpo) { this.writableEnded = true; this.cuerpo = cuerpo; resolver(); },
    cabeceras,
    fin,
  };
}

/* ------------------------------------------------------------ casos válidos */

describe('respuestas válidas', () => {
  test('«sí» con 2 acompañantes, autocar y alergias → 201 y se guarda normalizado', async () => {
    const datos = valido();
    const r = await enviar(datos);
    assert.equal(r.status, 201);
    assert.deepEqual(r.json, { ok: true });
    const f = buscar(datos.submission_id);
    assert.ok(f, 'la fila debe existir');
    assert.equal(f.nombre, 'Ana García López');
    assert.equal(f.asistencia, 'si');
    assert.equal(f.n_acompanantes, 2);
    assert.deepEqual(f.acompanantes, [{ nombre: 'Luis Pérez Gil' }, { nombre: 'Nuria Peña' }]);
    assert.equal(f.transporte_ida, 3);
    assert.equal(f.transporte_vuelta, 2);
    assert.deepEqual(f.alergias, [
      { persona: 'titular', nombre: 'Ana García López', opciones: ['sin_gluten', 'vegano'], otras: '' },
      { persona: 'acompanante_2', nombre: 'Nuria Peña', opciones: [], otras: 'Alergia al huevo' },
    ]);
    assert.equal(f.mensaje, '¡Qué ganas de veros!');
    assert.ok(!('web' in f) && !('t' in f), 'no se guardan campos técnicos');
    assert.ok(!('email' in f) && !('ip' in f), 'no se guarda correo ni IP');
  });

  test('«no» → 201; acompañantes/autocar/alergias se ignoran aunque lleguen', async () => {
    const datos = valido({ asistencia: 'no', mensaje: 'Os echaré de menos' });
    const r = await enviar(datos);
    assert.equal(r.status, 201);
    const f = buscar(datos.submission_id);
    assert.equal(f.asistencia, 'no');
    assert.equal(f.n_acompanantes, 0);
    assert.deepEqual(f.acompanantes, []);
    assert.equal(f.transporte_ida, 0);
    assert.equal(f.transporte_vuelta, 0);
    assert.deepEqual(f.alergias, []);
    assert.equal(f.mensaje, 'Os echaré de menos');
  });

  test('mínimo imprescindible (sin campos opcionales) → 201', async () => {
    const datos = { submission_id: randomUUID(), nombre: 'Pepe Ruiz', asistencia: 'si' };
    const r = await enviar(datos);
    assert.equal(r.status, 201);
    const f = buscar(datos.submission_id);
    assert.deepEqual([f.n_acompanantes, f.transporte_ida, f.transporte_vuelta, f.mensaje], [0, 0, 0, '']);
  });

  test('8 acompañantes y 9 plazas por trayecto (límites exactos) → 201', async () => {
    const acompanantes = Array.from({ length: 8 }, (_, i) => ({ nombre: `Invitado Número ${i + 1}` }));
    const datos = valido({ acompanantes, transporte: { ida: 9, vuelta: 9 }, alergias: [] });
    assert.equal((await enviar(datos)).status, 201);
    assert.equal(buscar(datos.submission_id).n_acompanantes, 8);
  });

  test('ñ, tildes y emoji se guardan intactos (y en Unicode NFC)', async () => {
    const datos = valido({
      nombre: 'Begon\u0303a Mun\u0303oz Ibáñez', // «ñ» descompuesta (n + tilde combinante)
      acompanantes: [{ nombre: 'Zoë Çelik 👩\u200D👩\u200D👧' }],
      transporte: { ida: 0, vuelta: 0 },
      alergias: [{ persona: 'acompanante_1', opciones: ['marisco'], otras: 'Pistachos 🥜' }],
      mensaje: '¡Enhorabuena! 🥂💍 Nos vemos en Valladolid ❤\uFE0F',
    });
    assert.equal((await enviar(datos)).status, 201);
    const f = buscar(datos.submission_id);
    assert.equal(f.nombre, 'Begoña Muñoz Ibáñez');
    assert.equal(f.nombre, f.nombre.normalize('NFC'));
    assert.equal(f.acompanantes[0].nombre, 'Zoë Çelik 👩\u200D👩\u200D👧');
    assert.equal(f.alergias[0].otras, 'Pistachos 🥜');
    assert.equal(f.mensaje, '¡Enhorabuena! 🥂💍 Nos vemos en Valladolid ❤\uFE0F');
  });

  test('HTML / scripts se guardan como texto literal, sin interpretar', async () => {
    const ataque = '<img src=x onerror=alert(1)><script>alert("x")</script>';
    const datos = valido({ nombre: `Ana ${ataque}`.slice(0, 120), mensaje: `${ataque} & "comillas" 'simples'` });
    const r = await enviar(datos);
    assert.equal(r.status, 201);
    assert.ok(!r.texto.includes('<script>'), 'la respuesta no repite lo enviado');
    const f = buscar(datos.submission_id);
    assert.equal(f.mensaje, `${ataque} & "comillas" 'simples'`);
    assert.ok(f.nombre.startsWith('Ana <img'));
  });

  test('limpieza: espacios, caracteres de control e invisibles; saltos de línea del mensaje', async () => {
    const datos = valido({
      nombre: '  Ana\u0000  \u200BGarcía\u202E\tLópez  ',
      acompanantes: [{ nombre: '\u00A0Luis\n\nPérez ' }],
      transporte: { ida: 1, vuelta: 1 },
      alergias: [{ persona: 'titular', opciones: ['vegano', 'vegano', 'sin_gluten'], otras: '  huevo\u0007 ' }],
      mensaje: '  Hola\r\n\r\n\r\n\r\nAdiós\u0000  ',
    });
    assert.equal((await enviar(datos)).status, 201);
    const f = buscar(datos.submission_id);
    assert.equal(f.nombre, 'Ana García López');
    assert.equal(f.acompanantes[0].nombre, 'Luis Pérez');
    assert.deepEqual(f.alergias[0].opciones, ['sin_gluten', 'vegano']); // sin repetidos, orden fijo
    assert.equal(f.alergias[0].otras, 'huevo');
    assert.equal(f.mensaje, 'Hola\n\nAdiós');
  });

  test('alergias vacías (nada marcado ni escrito) no se guardan', async () => {
    const datos = valido({
      alergias: [{ persona: 'titular', opciones: [], otras: '   ' }, { persona: 'acompanante_1', opciones: ['vegetariano'] }],
    });
    assert.equal((await enviar(datos)).status, 201);
    assert.deepEqual(buscar(datos.submission_id).alergias, [
      { persona: 'acompanante_1', nombre: 'Luis Pérez Gil', opciones: ['vegetariano'], otras: '' },
    ]);
  });

  test('Content-Type con charset es válido', async () => {
    const r = await enviar(valido(), { tipo: 'application/json; charset=utf-8' });
    assert.equal(r.status, 201);
  });

  test('sin «t» (campo opcional) también se acepta', async () => {
    const datos = valido();
    delete datos.t;
    assert.equal((await enviar(datos)).status, 201);
  });
});

/* ------------------------------------------------------------ idempotencia y antispam */

describe('duplicados y antispam', () => {
  test('mismo submission_id dos veces → 200 duplicado y una sola fila', async () => {
    const datos = valido();
    const r1 = await enviar(datos);
    const r2 = await enviar({ ...datos, asistencia: 'no' });
    assert.equal(r1.status, 201);
    assert.equal(r2.status, 200);
    assert.deepEqual(r2.json, { ok: true, duplicado: true });
    const iguales = filas().filter((f) => f.submission_id === datos.submission_id);
    assert.equal(iguales.length, 1);
    assert.equal(iguales[0].asistencia, 'si', 'el duplicado no sobrescribe');
  });

  test('envíos simultáneos con el mismo submission_id → una sola fila', async () => {
    const datos = valido();
    const rs = await Promise.all([enviar(datos), enviar(datos), enviar(datos)]);
    assert.deepEqual(rs.map((r) => r.status).sort(), [200, 200, 201]);
    assert.equal(filas().filter((f) => f.submission_id === datos.submission_id).length, 1);
  });

  test('trampa antispam rellena → 200 {ok:true} pero NO se guarda', async () => {
    const antes = filas().length;
    const datos = valido({ web: 'http://spam.example' });
    const r = await enviar(datos);
    assert.equal(r.status, 200);
    assert.deepEqual(r.json, { ok: true });
    assert.equal(filas().length, antes);
    assert.equal(buscar(datos.submission_id), undefined);
  });

  test('enviado demasiado rápido (t < 2500 ms) → 400 con aviso general, no se guarda', async () => {
    const datos = valido({ t: 900 });
    const r = await enviar(datos);
    assert.equal(r.status, 400);
    assert.match(r.json.errores.general, /demasiado rápido/);
    assert.equal(buscar(datos.submission_id), undefined);
  });
});

/* ------------------------------------------------------------ validación */

describe('validación (400 con mensajes en español)', () => {
  test('nombre vacío y acompañante sin nombre', async () => {
    const r = await enviar(valido({ nombre: '   ', acompanantes: [{ nombre: 'Luis Pérez' }, { nombre: '' }] }));
    assert.equal(r.status, 400);
    assert.equal(r.json.ok, false);
    assert.equal(r.json.errores.nombre, 'Escribe tu nombre y apellidos.');
    assert.equal(r.json.errores['acompanantes.1.nombre'], 'Escribe el nombre y apellidos del acompañante 2.');
  });

  test('nombre sin letras o de una sola letra', async () => {
    for (const nombre of ['1234', '!!', 'A']) {
      const r = await enviar(valido({ nombre }));
      assert.equal(r.status, 400, nombre);
      assert.equal(r.json.errores.nombre, 'Escribe un nombre válido.');
    }
  });

  test('nombre de más de 120 caracteres', async () => {
    const r = await enviar(valido({ nombre: 'A'.repeat(121) }));
    assert.equal(r.status, 400);
    assert.match(r.json.errores.nombre, /máximo 120/);
  });

  test('asistencia ausente o con valor raro', async () => {
    for (const asistencia of [undefined, 'quizas', 'sí', true]) {
      const r = await enviar(valido({ asistencia }));
      assert.equal(r.status, 400);
      assert.equal(r.json.errores.asistencia, 'Indica si podrás asistir.');
    }
  });

  test('plazas de autocar por encima de 1 + acompañantes', async () => {
    const r = await enviar(valido({ acompanantes: [{ nombre: 'Luis Pérez' }], alergias: [], transporte: { ida: 3, vuelta: 2 } }));
    assert.equal(r.status, 400);
    assert.equal(r.json.errores['transporte.ida'], 'Como máximo 2 plazas (tú y tus acompañantes).');
    assert.equal(r.json.errores['transporte.vuelta'], undefined);
    const r2 = await enviar(valido({ acompanantes: [], alergias: [], transporte: { ida: 0, vuelta: 2 } }));
    assert.equal(r2.json.errores['transporte.vuelta'], 'Como máximo 1 plaza (la tuya).');
  });

  test('plazas no enteras, negativas o de tipo incorrecto', async () => {
    for (const ida of [-1, 1.5, '2', 10, true, {}]) {
      const r = await enviar(valido({ transporte: { ida, vuelta: 0 } }));
      assert.equal(r.status, 400, String(ida));
      assert.ok(r.json.errores['transporte.ida'], String(ida));
    }
  });

  test('más de 8 acompañantes o lista con formato incorrecto', async () => {
    const nueve = Array.from({ length: 9 }, (_, i) => ({ nombre: `Persona ${i + 1}` }));
    let r = await enviar(valido({ acompanantes: nueve, transporte: { ida: 0, vuelta: 0 }, alergias: [] }));
    assert.equal(r.status, 400);
    assert.match(r.json.errores.acompanantes, /máximo 8/);
    r = await enviar(valido({ acompanantes: 'Luis', alergias: [] }));
    assert.equal(r.status, 400);
    assert.ok(r.json.errores.acompanantes);
  });

  test('alergias: persona inexistente, repetida u opción desconocida', async () => {
    let r = await enviar(valido({ alergias: [{ persona: 'acompanante_3', opciones: ['vegano'] }] }));
    assert.equal(r.status, 400);
    assert.ok(r.json.errores.alergias);
    r = await enviar(valido({ alergias: [{ persona: 'titular', opciones: [] , otras: 'x'}, { persona: 'titular', opciones: ['vegano'] }] }));
    assert.equal(r.status, 400);
    r = await enviar(valido({ alergias: [{ persona: 'titular', opciones: ['picante'] }] }));
    assert.equal(r.status, 400);
    assert.ok(r.json.errores['alergias.titular']);
  });

  test('longitudes: mensaje > 1000 y «otras» > 300 (1000/300 exactos sí valen)', async () => {
    let r = await enviar(valido({ mensaje: 'x'.repeat(1001) }));
    assert.equal(r.status, 400);
    assert.match(r.json.errores.mensaje, /máximo 1000/);
    r = await enviar(valido({ alergias: [{ persona: 'titular', opciones: [], otras: 'y'.repeat(301) }] }));
    assert.equal(r.status, 400);
    assert.match(r.json.errores['alergias.titular.otras'], /máximo 300/);
    const ok = valido({ mensaje: 'x'.repeat(1000), alergias: [{ persona: 'titular', opciones: [], otras: 'y'.repeat(300) }] });
    assert.equal((await enviar(ok)).status, 201);
  });

  test('submission_id ausente o mal formado', async () => {
    for (const submission_id of [undefined, '', 'abc', 123]) {
      const r = await enviar(valido({ submission_id }));
      assert.equal(r.status, 400);
      assert.ok(r.json.errores.submission_id);
    }
  });

  test('cuerpo que no es un objeto (lista, número, null)', async () => {
    for (const cuerpo of ['[]', '42', 'null', '"hola"']) {
      const r = await enviar(cuerpo);
      assert.equal(r.status, 400, cuerpo);
      assert.equal(r.json.ok, false);
    }
  });
});

/* ------------------------------------------------------------ protocolo HTTP */

describe('protocolo', () => {
  test('métodos distintos de POST → 405 con Allow: POST', async () => {
    for (const metodo of ['GET', 'PUT', 'DELETE', 'PATCH']) {
      const r = await enviar(valido(), { metodo });
      assert.equal(r.status, 405, metodo);
      assert.equal(r.headers.get('allow'), 'POST');
    }
  });

  test('Content-Type distinto de JSON → 415', async () => {
    for (const tipo of ['text/plain', 'application/x-www-form-urlencoded', 'multipart/form-data; boundary=x', null]) {
      const r = await enviar(JSON.stringify(valido()), { tipo });
      assert.equal(r.status, 415, String(tipo));
    }
  });

  test('JSON mal formado → 400', async () => {
    const r = await enviar('{"nombre": "Ana",');
    assert.equal(r.status, 400);
    assert.equal(r.json.ok, false);
  });

  test('cuerpo enorme (> 20 KB) → 413, con y sin Content-Length', async () => {
    const enorme = valido({ mensaje: 'x'.repeat(25 * 1024) });
    const r = await enviar(enorme);
    assert.equal(r.status, 413);
    assert.equal(buscar(enorme.submission_id), undefined);

    // Sin Content-Length (transferencia por trozos): se corta al pasar de 20 KB
    const status = await new Promise((resolve, reject) => {
      const u = new URL(srv.url + '/api/rsvp');
      const req = http.request({ hostname: u.hostname, port: u.port, path: u.pathname, method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Transfer-Encoding': 'chunked' } }, (res) => { res.resume(); resolve(res.statusCode); });
      req.on('error', reject);
      for (let i = 0; i < 30; i++) req.write('x'.repeat(1024));
      req.end();
    });
    assert.equal(status, 413);
  });

  test('las respuestas de la API no se cachean', async () => {
    const r = await enviar(valido());
    assert.equal(r.headers.get('cache-control'), 'no-store');
    assert.match(r.headers.get('content-type'), /application\/json/);
  });
});

/* ------------------------------------------------------------ Supabase caído o mal configurado */

describe('errores de Supabase → 503 sin filtrar detalles', () => {
  test('Supabase no responde (conexión rechazada)', async () => {
    await conEntorno({ SUPABASE_URL: 'http://127.0.0.1:1' }, async () => {
      const r = await enviar(valido());
      assert.equal(r.status, 503);
      assert.equal(r.json.ok, false);
      assert.match(r.json.error, /No hemos podido guardar tu respuesta/);
      assert.ok(!/ECONN|stack|at |sb_secret|127\.0\.0\.1/.test(r.texto), 'no filtra detalles técnicos');
    });
  });

  test('faltan las variables de entorno', async () => {
    await conEntorno({ SUPABASE_URL: undefined, SUPABASE_SECRET_KEY: undefined }, async () => {
      const r = await enviar(valido());
      assert.equal(r.status, 503);
      assert.match(r.json.error, /No hemos podido guardar/);
    });
  });

  test('clave equivocada (Supabase responde 401) o pública', async () => {
    for (const clave of ['sb_secret_equivocada', 'sb_publishable_abc']) {
      await conEntorno({ SUPABASE_SECRET_KEY: clave }, async () => {
        const r = await enviar(valido());
        assert.equal(r.status, 503, clave);
        assert.ok(!r.texto.includes(clave), 'nunca devuelve la clave');
      });
    }
  });

  test('la tabla no existe (schema.sql sin ejecutar)', async () => {
    await conEntorno({ SUPABASE_URL: `${srv.url}/__supabase/otra-ruta` }, async () => {
      const r = await enviar(valido());
      assert.equal(r.status, 503);
    });
  });
});

/* ------------------------------------------------------------ cabeceras hacia Supabase */

describe('petición a PostgREST', () => {
  async function capturar(cambios) {
    const recibidas = [];
    const falso = http.createServer((req, res) => {
      let cuerpo = '';
      req.on('data', (t) => { cuerpo += t; });
      req.on('end', () => {
        recibidas.push({ url: req.url, headers: req.headers, cuerpo });
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify([{ submission_id: 'x' }]));
      });
    });
    await new Promise((r) => falso.listen(0, '127.0.0.1', r));
    try {
      await conEntorno({ SUPABASE_URL: `http://127.0.0.1:${falso.address().port}`, ...cambios }, () => enviar(valido()));
    } finally {
      await new Promise((r) => falso.close(r));
    }
    return recibidas[0];
  }

  test('clave nueva sb_secret_: solo en «apikey», nunca en Authorization', async () => {
    const p = await capturar({ SUPABASE_SECRET_KEY: 'sb_secret_prueba123' });
    assert.equal(p.headers.apikey, 'sb_secret_prueba123');
    assert.equal(p.headers.authorization, undefined);
    assert.equal(p.url, '/rest/v1/rsvps?on_conflict=submission_id&select=submission_id');
    assert.match(p.headers.prefer, /resolution=ignore-duplicates/);
    assert.match(p.headers.prefer, /return=representation/);
    const cuerpo = JSON.parse(p.cuerpo);
    assert.deepEqual(Object.keys(cuerpo).sort(), ['acompanantes', 'alergias', 'asistencia', 'mensaje', 'n_acompanantes',
      'nombre', 'submission_id', 'transporte_ida', 'transporte_vuelta', 'user_agent'].sort());
  });

  test('clave antigua service_role (JWT): apikey + Authorization: Bearer', async () => {
    const jwt = 'eyJhbGciOiJIUzI1NiJ9.' + Buffer.from('{"role":"service_role"}').toString('base64url') + '.firma';
    const p = await capturar({ SUPABASE_SECRET_KEY: undefined, SUPABASE_SERVICE_ROLE_KEY: jwt });
    assert.equal(p.headers.apikey, jwt);
    assert.equal(p.headers.authorization, `Bearer ${jwt}`);
  });
});

/* ------------------------------------------------------------ Vercel (cuerpo ya leído) */

describe('compatibilidad con los «helpers» de Vercel', () => {
  test('req.body ya parseado por Vercel → 201', async () => {
    const datos = valido();
    const res = resFalso();
    await manejadorRsvp(reqVercel({ body: datos }), res);
    await res.fin;
    assert.equal(res.statusCode, 201);
    assert.ok(buscar(datos.submission_id));
  });

  test('req.body que lanza (JSON inválido en Vercel) → 400', async () => {
    const res = resFalso();
    await manejadorRsvp(reqVercel({ cuerpoLanza: true }), res);
    assert.equal(res.statusCode, 400);
  });

  test('req.body enorme ya parseado → 413', async () => {
    const res = resFalso();
    await manejadorRsvp(reqVercel({ body: valido({ mensaje: 'x'.repeat(30000) }) }), res);
    assert.equal(res.statusCode, 413);
  });
});

/* ------------------------------------------------------------ panel de los novios */

describe('/api/admin', () => {
  const TOKEN = 'una-contraseña-larga-ñ-2027';
  const pedir = (token, metodo = 'GET') => enviar(null, {
    ruta: '/api/admin', metodo, tipo: null,
    cabeceras: token === null ? {} : { Authorization: `Bearer ${encodeURIComponent(token)}` },
  });

  test('sin ADMIN_TOKEN (o demasiado corto) → 404', async () => {
    await conEntorno({ ADMIN_TOKEN: undefined }, async () => assert.equal((await pedir('loquesea')).status, 404));
    await conEntorno({ ADMIN_TOKEN: 'corto' }, async () => assert.equal((await pedir('corto')).status, 404));
  });

  test('contraseña incorrecta o ausente → 401 tras una pequeña espera', async () => {
    await conEntorno({ ADMIN_TOKEN: TOKEN }, async () => {
      const t0 = Date.now();
      const r = await pedir('otra-contraseña-larga');
      assert.equal(r.status, 401);
      assert.ok(Date.now() - t0 >= 550, 'debe esperar antes de responder');
      assert.equal((await pedir(null)).status, 401);
      assert.equal(r.headers.get('cache-control'), 'no-store, private');
    });
  });

  test('contraseña correcta (con ñ) → 200 con resumen y respuestas marcadas', async () => {
    await conEntorno({ ADMIN_TOKEN: TOKEN }, async () => {
      const r = await pedir(TOKEN);
      assert.equal(r.status, 200);
      assert.equal(r.json.ok, true);
      assert.equal(r.headers.get('cache-control'), 'no-store, private');
      assert.ok(Array.isArray(r.json.respuestas) && r.json.respuestas.length > 0);
      assert.ok(r.json.respuestas.every((f) => typeof f.vigente === 'boolean' && f.n_respuestas >= 1));
      assert.ok(!('user_agent' in r.json.respuestas[0]) && !('submission_id' in r.json.respuestas[0]));
      for (const k of ['respuestas_recibidas', 'respuestas_vigentes', 'confirman_si', 'no_asisten', 'personas_asisten',
        'plazas_ida', 'plazas_vuelta', 'alergias', 'otras_alergias']) assert.ok(k in r.json.resumen, k);
    });
  });

  test('solo GET → 405', async () => {
    await conEntorno({ ADMIN_TOKEN: TOKEN }, async () => {
      assert.equal((await pedir(TOKEN, 'POST')).status, 405);
    });
  });

  test('Supabase caído → 503 con diagnóstico comprensible', async () => {
    await conEntorno({ ADMIN_TOKEN: TOKEN, SUPABASE_URL: 'http://127.0.0.1:1' }, async () => {
      const r = await pedir(TOKEN);
      assert.equal(r.status, 503);
      assert.match(r.json.error, /Supabase/);
    });
  });
});

describe('/api/ping', () => {
  test('consulta mínima → 200; con CRON_SECRET exige la cabecera', async () => {
    assert.equal((await enviar(null, { ruta: '/api/ping', metodo: 'GET', tipo: null })).status, 200);
    await conEntorno({ CRON_SECRET: 'secreto-del-cron-123' }, async () => {
      assert.equal((await enviar(null, { ruta: '/api/ping', metodo: 'GET', tipo: null })).status, 401);
      const ok = await enviar(null, { ruta: '/api/ping', metodo: 'GET', tipo: null, cabeceras: { Authorization: 'Bearer secreto-del-cron-123' } });
      assert.equal(ok.status, 200);
    });
  });
});

/* ------------------------------------------------------------ cálculos del panel (= vistas SQL) */

describe('respuestas vigentes y resumen', () => {
  test('normalización del nombre igual que en schema.sql', () => {
    assert.equal(normalizarNombre('  ANA   García  López '), 'ana garcia lopez');
    assert.equal(normalizarNombre('Pedro SÁNCHEZ Ñúñez'), 'pedro sanchez nunez');
    assert.equal(normalizarNombre('Zoë Çelik'), 'zoe celik');
  });

  test('la última respuesta de cada persona manda; el resumen cuenta solo esas', () => {
    const filasDemo = [
      { created_at: '2027-01-01T10:00:00Z', nombre: 'Ana García', asistencia: 'si', n_acompanantes: 2, transporte_ida: 3, transporte_vuelta: 3,
        alergias: [{ persona: 'titular', opciones: ['vegano'], otras: '' }] },
      { created_at: '2027-01-05T10:00:00Z', nombre: 'ana  garcia', asistencia: 'no', n_acompanantes: 0, transporte_ida: 0, transporte_vuelta: 0, alergias: [] },
      { created_at: '2027-01-02T10:00:00Z', nombre: 'José Muñoz', asistencia: 'si', n_acompanantes: 1, transporte_ida: 2, transporte_vuelta: 1,
        alergias: [{ persona: 'acompanante_1', opciones: ['sin_lactosa', 'marisco'], otras: 'huevo' }] },
    ];
    const marcadas = marcarVigentes(filasDemo);
    assert.deepEqual(marcadas.map((f) => [f.nombre, f.vigente, f.n_respuestas]), [
      ['ana  garcia', true, 2], ['José Muñoz', true, 1], ['Ana García', false, 2],
    ]);
    const r = calcularResumen(marcadas);
    assert.equal(r.respuestas_recibidas, 3);
    assert.equal(r.respuestas_vigentes, 2);
    assert.equal(r.confirman_si, 1);
    assert.equal(r.no_asisten, 1);
    assert.equal(r.personas_asisten, 2);
    assert.equal(r.plazas_ida, 2);
    assert.equal(r.plazas_vuelta, 1);
    assert.deepEqual(r.alergias, { sin_gluten: 0, sin_lactosa: 1, vegetariano: 0, vegano: 0, frutos_secos: 0, marisco: 1 });
    assert.equal(r.otras_alergias, 1);
    assert.equal(r.personas_con_alergias, 1);
  });

  test('limpiarLinea quita controles e invisibles pero conserva emojis compuestos', () => {
    assert.equal(limpiarLinea('a\u0000b\u200Bc\u202Ed 👨\u200D👩\u200D👧 '), 'a bcd 👨\u200D👩\u200D👧');
  });
});
