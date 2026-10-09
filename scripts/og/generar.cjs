// Genera la imagen que se ve al compartir el enlace (WhatsApp, etc.): public/assets/img/og.jpg, 1200×630.
// Usa la propia portada (misma tipografía, papel y foto) con la cuenta atrás y el botón ocultos y los nombres más grandes.
//   node scripts/og/generar.cjs            (con Playwright instalado; PLAYWRIGHT_PATH=/ruta/a/playwright y CHROME_PATH si hace falta)
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const RAIZ = path.resolve(__dirname, '..', '..');
const SALIDA = path.join(RAIZ, 'public', 'assets', 'img', 'og.jpg');

(async () => {
  const navegador = await chromium.launch({
    executablePath: process.env.CHROME_PATH || undefined,
    args: ['--no-sandbox', '--allow-file-access-from-files'],
  });
  const pagina = await navegador.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  await pagina.goto('file://' + path.join(RAIZ, 'public', 'index.html') + '?intro=0', { waitUntil: 'load' });
  await pagina.addStyleTag({ content: `
    html .portada { --n: 540px; --foto: 400px; --alto: 630px; min-height: 630px; height: 630px; column-gap: 70px; row-gap: 0; padding-block: 0; }
    html .portada__texto { align-self: center; gap: 14px; }
    html .portada__extra, html .portada__baja, html .portada__ruta { display: none; }
    html .portada__aviso { font-size: 15px; letter-spacing: .34em; }
    html .portada__fecha { font-size: 16px; margin-top: 18px; }
    html .portada__foto { align-self: center; }
  ` });
  await pagina.evaluate(() => document.fonts.ready);
  await pagina.waitForFunction(() => { const i = document.querySelector('.ventana img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
  await pagina.waitForTimeout(600);
  await pagina.screenshot({ path: SALIDA, type: 'jpeg', quality: 84 });
  await navegador.close();
  console.log('Escrito', path.relative(RAIZ, SALIDA));
})().catch((e) => { console.error(e); process.exit(1); });
