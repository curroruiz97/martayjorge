const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const fs = require('fs');
(async () => {
  const svg = fs.readFileSync('nombres.svg.html', 'utf8');
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 1200 } });
  await p.setContent('<style>.tz{display:none}.rl{fill:#000}</style><div style="width:1000px">' + svg + '</div>');
  const bb = await p.evaluate(() => { const s = document.querySelector('svg'); const g = [...s.children].filter((e) => e.tagName === 'g'); let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const e of s.querySelectorAll('use.rl')) { const r = e.getBoundingClientRect(); const sr = s.getBoundingClientRect(); const k = s.viewBox.baseVal.width / sr.width; const ax = (r.left - sr.left) * k + s.viewBox.baseVal.x, ay = (r.top - sr.top) * k + s.viewBox.baseVal.y, bx = (r.right - sr.left) * k + s.viewBox.baseVal.x, by = (r.bottom - sr.top) * k + s.viewBox.baseVal.y; x0 = Math.min(x0, ax); y0 = Math.min(y0, ay); x1 = Math.max(x1, bx); y1 = Math.max(y1, by); } return [x0, y0, x1, y1]; });
  console.log(JSON.stringify(bb.map(Math.round)));
  await b.close();
})();
