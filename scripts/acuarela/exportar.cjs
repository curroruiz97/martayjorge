// Convierte cada SVG de acuarela en PNG con fondo transparente (a la anchura pedida) con Chromium.
//   node exportar.cjs <carpeta_con_svg> <carpeta_salida> <ancho1,ancho2,...>
// (PLAYWRIGHT_PATH=/ruta/a/playwright y CHROME_PATH si hacen falta)
const fs = require('fs'), path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
(async () => {
  const [ent, sal, anchos] = [process.argv[2], process.argv[3], (process.argv[4] || '800').split(',').map(Number)];
  fs.mkdirSync(sal, { recursive: true });
  const navegador = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox'] });
  for (const f of fs.readdirSync(ent).filter((x) => x.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(ent, f), 'utf8');
    const m = svg.match(/width="(\d+)" height="(\d+)"/);
    const [w, h] = [+m[1], +m[2]];
    for (const ancho of anchos) {
      const dpr = ancho / w;
      const pagina = await navegador.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
      await pagina.setContent('<!doctype html><style>html,body{margin:0;background:transparent}</style>' + svg);
      await pagina.waitForTimeout(400);
      await pagina.screenshot({ path: path.join(sal, f.replace('.svg', `-${ancho}.png`)), omitBackground: true });
      await pagina.close();
    }
  }
  await navegador.close();
})();
