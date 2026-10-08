// Genera el ornamento de la portada a partir de la ruta de la ilustradora:
//  - rayas individuales (cada una con su retardo, para que aparezcan en la estela del avión)
//  - fotogramas CSS del vuelo del avión (posición+rotación muestreadas, con la misma curva de easing)
// Uso: node ornamento.cjs <ruta-horizontal.svg> <salida_dir> [duracion_s=2.1] [retardo_s=0.2]
const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const [svgFile, outDir, durArg, delayArg] = process.argv.slice(2);
const DUR = parseFloat(durArg || '2.1');
const BASE = parseFloat(delayArg || '0.2');
const EASE = [0.42, 0.0, 0.28, 1.0]; // cubic-bezier del vuelo (suave al salir y al llegar)

// cubic-bezier(x1,y1,x2,y2): progreso(t) y su inversa
function bez(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = (t) => ((ax * t + bx) * t + cx) * t;
  const Y = (t) => ((ay * t + by) * t + cy) * t;
  const solveT = (x) => { let lo = 0, hi = 1; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (X(m) < x) lo = m; else hi = m; } return (lo + hi) / 2; };
  return { p: (u) => Y(solveT(u)), inv: (s) => { let lo = 0, hi = 1; for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (Y(solveT(m)) < s) lo = m; else hi = m; } return (lo + hi) / 2; } };
}
const ease = bez(...EASE);

(async () => {
  const svg = fs.readFileSync(svgFile, 'utf8');
  const d = svg.match(/id="ruta"[^>]*\sd="([^"]+)"/)[1];
  const dash = svg.match(/id="ruta"[^>]*stroke-dasharray="([^"]+)"/)[1].split(/\s+/).map(Number);
  const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const planeInner = svg.match(/<g id="avion"[^>]*>([\s\S]*?)<\/g>/)[1];

  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.setContent(`<svg xmlns="http://www.w3.org/2000/svg"><path id="r" d="${d}"/></svg>`);
  const data = await p.evaluate(() => {
    const r = document.getElementById('r');
    const L = r.getTotalLength();
    const pts = [];
    for (let s = 0; s <= L + 0.01; s += 0.5) { const q = r.getPointAtLength(Math.min(s, L)); pts.push([q.x, q.y]); }
    return { L, pts };
  });
  await b.close();
  const { L, pts } = data;
  const at = (s) => { const i = Math.min(pts.length - 1, Math.max(0, s / 0.5)); const i0 = Math.floor(i), i1 = Math.min(pts.length - 1, i0 + 1), f = i - i0; return [pts[i0][0] * (1 - f) + pts[i1][0] * f, pts[i0][1] * (1 - f) + pts[i1][1] * f]; };
  const f1 = (v) => (Math.round(v * 10) / 10).toString();

  // ---- rayas ----
  const dashes = [];
  let s = 0, k = 0;
  while (s < L) {
    const len = dash[k % dash.length];
    if (k % 2 === 0) dashes.push([s, Math.min(L, s + len)]);
    s += len; k++;
  }
  const lastIdx = dashes.length;
  const dashSvg = dashes.map(([a, z], i) => {
    const seg = [];
    for (let q = a; q < z; q += 1.5) seg.push(at(q));
    seg.push(at(z));
    const dd = 'M' + seg.map((pt) => f1(pt[0]) + ' ' + f1(pt[1])).join('L');
    // aparece en la estela: cuando el avión ha pasado por el final de la raya
    const u = ease.inv(Math.min(1, (z + 4) / L));
    const delay = BASE + u * DUR;
    return `<path class="rz" pathLength="1" style="--d:${delay.toFixed(2)}s" d="${dd}"/>`;
  }).join('');

  // ---- vuelo del avión ----
  const N = 56;
  let prevAng = null, off = 0;
  const frames = [];
  const pose = (u) => {
    const sPos = L * ease.p(u);
    const a = at(Math.max(0, sPos - 1.2)), c = at(Math.min(L, sPos + 1.2)), q = at(sPos);
    let ang = Math.atan2(c[1] - a[1], c[0] - a[0]) * 180 / Math.PI + off;
    if (prevAng !== null) { while (ang - prevAng > 180) { ang -= 360; off -= 360; } while (ang - prevAng < -180) { ang += 360; off += 360; } }
    prevAng = ang;
    return { x: q[0], y: q[1], a: ang };
  };
  for (let i = 0; i <= N; i++) { const u = i / N; const ps = pose(u); frames.push(`${(u * 100).toFixed(1)}%{transform:translate(${f1(ps.x)}px,${f1(ps.y)}px) rotate(${f1(ps.a)}deg)}`); }
  const fin = pose(1);
  const css = `/* GENERADO por scripts/intro/ornamento.cjs · no editar a mano */
@keyframes vuelo-portada{${frames.join('')}}
.avion-h{transform:translate(${f1(fin.x)}px,${f1(fin.y)}px) rotate(${f1(fin.a % 360)}deg)}
.js .avion-h,.avion-h{animation:vuelo-portada ${DUR}s linear ${BASE}s backwards}
`;
  const out = `<svg class="portada__ruta-svg" viewBox="${vb[0]} ${vb[1]} ${vb[2]} ${vb[3]}" aria-hidden="true" focusable="false"><g class="rz-g">${dashSvg}</g><g class="avion-h" stroke="#2b2a28" stroke-linecap="round" stroke-linejoin="round">${planeInner}</g></svg>`;
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'ornamento.svg.html'), out);
  fs.writeFileSync(path.join(outDir, 'ornamento.css'), css);
  console.log(`largo ${L.toFixed(1)} · rayas ${dashes.length} · svg ${(out.length / 1024).toFixed(1)} KB · css ${(css.length / 1024).toFixed(1)} KB · pose final ${JSON.stringify(fin)}`);
})();
