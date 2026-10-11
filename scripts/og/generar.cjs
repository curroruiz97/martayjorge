// Genera dos imágenes con Chromium:
//   · la que se ve al compartir el enlace (WhatsApp, etc.): public/assets/img/og.jpg, 1200×630. Usa la propia portada (mismos
//     nombres pintados a pincel, lino y foto con el borde a pincel) en dos columnas, sin la cuenta atrás ni el botón.
//   · con --icono, también el icono de la pantalla de inicio del móvil: public/assets/img/apple-touch-icon.png, 180×180 (el
//     lazo con el avión de la V1, en rojo, sobre el lino con una pareja de rayas). En la V2 no se ha cambiado.
//   node scripts/og/generar.cjs [--icono]   (con Playwright instalado; PLAYWRIGHT_PATH=/ruta/a/playwright y CHROME_PATH si hace falta)
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const RAIZ = path.resolve(__dirname, '..', '..');
const SALIDA = path.join(RAIZ, 'public', 'assets', 'img', 'og.jpg');
const ICONO = path.join(RAIZ, 'public', 'assets', 'img', 'apple-touch-icon.png');
const fs = require('fs');

(async () => {
  const navegador = await chromium.launch({
    executablePath: process.env.CHROME_PATH || undefined,
    args: ['--no-sandbox', '--allow-file-access-from-files'],
  });
  const pagina = await navegador.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await pagina.goto('file://' + path.join(RAIZ, 'public', 'index.html') + '?intro=0', { waitUntil: 'load' });
  await pagina.addStyleTag({ content: `
    html .portada { --n: 560px; --alto: 630px; min-height: 630px; height: 630px; width: 1200px;
      grid-template-columns: 600px 432px; grid-template-areas: "texto foto"; grid-template-rows: auto;
      column-gap: 56px; row-gap: 0; align-content: center; justify-content: center; padding: 0 40px; }
    html .portada__texto { align-self: center; gap: 12px; }
    html .portada__extra { display: none; }
    html .portada__aviso { font-size: 24px; }
    html .portada__fecha { margin-top: 22px; }
    html .portada__fecha time { font-size: 34px; }
    html .portada__ciudad { font-size: 25px; }
    html .portada__foto { align-self: center; justify-self: center; margin: 0; width: 432px; height: 540px; }
  ` });
  await pagina.evaluate(() => document.fonts.ready);
  await pagina.waitForFunction(() => { const i = document.querySelector('.portada__foto img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
  await pagina.waitForTimeout(600);
  await pagina.screenshot({ path: SALIDA, type: 'jpeg', quality: 84 });
  console.log('Escrito', path.relative(RAIZ, SALIDA));
  if (!process.argv.includes('--icono')) { await navegador.close(); return; }

  // ---- icono 180×180 ----
  const favicon = fs.readFileSync(path.join(RAIZ, 'public', 'assets', 'ilustraciones', 'favicon.svg'), 'utf8')
    .replace(/<style>.*?<\/style>/s, '<style>.t{stroke:#a3121d}.f{fill:#a3121d}</style>');
  const lino = 'file://' + path.join(RAIZ, 'public', 'assets', 'img', 'lino.webp');
  const icono = await navegador.newPage({ viewport: { width: 180, height: 180 }, deviceScaleFactor: 1 });
  await icono.setContent(`<!doctype html><style>
    html, body { margin: 0; width: 180px; height: 180px; overflow: hidden; }
    body { background-color: #fbf9f1;
      background-image: url("${lino}"), linear-gradient(90deg, transparent 0, transparent 39%, rgba(238,200,190,.18) 40.6%, rgba(238,200,190,.18) 47.6%, rgba(246,226,218,.07) 49%, rgba(246,226,218,.07) 51%, rgba(238,200,190,.18) 52.4%, rgba(238,200,190,.18) 59.4%, transparent 61%, transparent 100%);
      background-size: 128px 128px, 180px 100%; background-position: 0 0, 50% 0; background-repeat: repeat, no-repeat; background-blend-mode: multiply, normal; }
    svg { position: absolute; left: 24px; top: 24px; width: 132px; height: 132px; }
  </style>${favicon}`);
  await icono.waitForTimeout(500);
  await icono.screenshot({ path: ICONO, type: 'png' });
  await navegador.close();
  console.log('Escrito', path.relative(RAIZ, ICONO));
})().catch((e) => { console.error(e); process.exit(1); });
