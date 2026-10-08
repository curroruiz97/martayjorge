/* Marta & Jorge · comportamiento de la página (sin dependencias).
   Cuenta atrás, revelado al hacer scroll, ilustraciones que se dibujan,
   avión que vuela por la ruta, copiar IBAN y botón de contacto. */
(() => {
  'use strict';

  const root = document.documentElement;
  const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const NS = 'http://www.w3.org/2000/svg';

  /* ---------- Utilidades ---------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
  const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

  /** Ejecuta fn cuando el elemento entra en pantalla (una sola vez). */
  function alEntrar(el, fn, opciones = {}) {
    if (!('IntersectionObserver' in window)) { fn(); return; }
    const io = new IntersectionObserver((entradas) => {
      if (entradas.some((e) => e.isIntersecting)) { io.disconnect(); fn(); }
    }, { threshold: 0.2, rootMargin: '0px 0px -6% 0px', ...opciones });
    io.observe(el);
  }

  let toastTimer;
  function avisar(texto) {
    const el = $('#aviso');
    if (!el) return;
    el.textContent = texto;
    el.hidden = false;
    void el.offsetWidth; // fuerza el reflujo para que la transición arranque
    el.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.classList.remove('visible');
      setTimeout(() => { el.hidden = true; }, 400);
    }, 2400);
  }

  /* ---------- Tipografías listas: arranca la "escritura" de los nombres ---------- */
  function initFuentes() {
    const listo = () => root.classList.add('fuentes-listas');
    if (!document.fonts || !document.fonts.ready) { listo(); return; }
    Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 2500))]).then(listo);
  }

  /* ---------- Revelado al hacer scroll ---------- */
  function initRevelado() {
    const els = $$('.revelar');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('visible')); return; }
    const io = new IntersectionObserver((entradas) => {
      entradas.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    els.forEach((e) => io.observe(e));
  }

  /* ---------- Cuenta atrás (días · horas · minutos; sin segundos para que sea sobria) ---------- */
  function initCuenta() {
    const caja = $('[data-cuenta]');
    if (!caja) return;
    const objetivo = new Date(caja.dataset.cuenta).getTime();
    if (Number.isNaN(objetivo)) return;
    const num = { d: $('[data-u="d"]', caja), h: $('[data-u="h"]', caja), m: $('[data-u="m"]', caja) };
    const txt = { d: $('[data-l="d"]', caja), h: $('[data-l="h"]', caja), m: $('[data-l="m"]', caja) };
    const fila = $('.cuenta__fila', caja);
    const estado = $('.cuenta__estado', caja);
    const sr = $('[data-cuenta-sr]', caja);
    const pad = (n) => String(n).padStart(2, '0');

    function pintar() {
      const resto = objetivo - Date.now();
      if (resto <= 0) {
        const pasado = -resto;
        fila.hidden = true;
        estado.hidden = false;
        estado.textContent = pasado < 12 * 3600e3 ? '¡Hoy es el gran día!' : '¡Gracias por celebrarlo con nosotros!';
        sr.textContent = estado.textContent;
        return pasado < 12 * 3600e3; // sigue vivo solo durante el día de la boda
      }
      const d = Math.floor(resto / 864e5);
      const h = Math.floor((resto % 864e5) / 36e5);
      const m = Math.floor((resto % 36e5) / 6e4);
      num.d.textContent = d;
      num.h.textContent = pad(h);
      num.m.textContent = pad(m);
      txt.d.textContent = d === 1 ? 'día' : 'días';
      txt.h.textContent = h === 1 ? 'hora' : 'horas';
      txt.m.textContent = 'min';
      sr.textContent = `Faltan ${d} ${d === 1 ? 'día' : 'días'}, ${h} ${h === 1 ? 'hora' : 'horas'} y ${m} minutos para la boda.`;
      return true;
    }
    if (pintar()) {
      const id = setInterval(() => { if (!pintar()) clearInterval(id); }, 20000);
    }
  }

  /* ---------- Ilustraciones SVG: se incrustan para poder animarlas ---------- */
  async function cargarSvg(caja) {
    const url = caja.dataset.svg;
    try {
      const r = await fetch(url, { credentials: 'same-origin' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const doc = new DOMParser().parseFromString(await r.text(), 'image/svg+xml');
      const svg = doc.documentElement;
      if (!svg || svg.localName !== 'svg' || doc.querySelector('parsererror')) throw new Error('SVG no válido');
      $$('script, style, foreignObject, iframe, object, embed', svg).forEach((n) => n.remove());
      // defensa extra: fuera atributos de eventos (onload, onclick…) por si algún SVG se editara a mano
      $$('*', svg).forEach((n) => Array.from(n.attributes).forEach((a) => { if (/^on/i.test(a.name)) n.removeAttribute(a.name); }));
      svg.removeAttribute('width');
      svg.removeAttribute('height');
      svg.setAttribute('focusable', 'false');
      svg.setAttribute('aria-hidden', 'true');
      const importado = document.importNode(svg, true);
      caja.appendChild(importado);
      return importado;
    } catch (err) {
      console.warn('No se pudo cargar la ilustración', url, err);
      return null;
    }
  }

  function prepararTrazos(svg) {
    const trazos = $$('.l', svg);
    const n = Math.max(1, trazos.length);
    trazos.forEach((p, i) => {
      if (!p.hasAttribute('pathLength')) p.setAttribute('pathLength', '1');
      p.style.transitionDelay = ((i / n) * 1.3).toFixed(3) + 's';
    });
  }

  /** Avión que recorre #ruta mientras la línea discontinua se va dibujando. */
  function prepararRuta(svg) {
    const ruta = $('#ruta', svg);
    const avion = $('#avion', svg);
    if (!ruta || !avion || typeof ruta.getTotalLength !== 'function') return null;
    const largo = ruta.getTotalLength();
    if (!largo) return null;

    // Máscara: una copia gruesa y continua de la ruta que se "descubre" poco a poco.
    const vb = svg.viewBox.baseVal;
    let defs = $('defs', svg);
    if (!defs) { defs = document.createElementNS(NS, 'defs'); svg.insertBefore(defs, svg.firstChild); }
    const idMascara = 'mascara-ruta-' + Math.random().toString(36).slice(2, 8);
    const mascara = document.createElementNS(NS, 'mask');
    mascara.setAttribute('id', idMascara);
    mascara.setAttribute('maskUnits', 'userSpaceOnUse');
    mascara.setAttribute('x', vb.x - 60); mascara.setAttribute('y', vb.y - 60);
    mascara.setAttribute('width', vb.width + 120); mascara.setAttribute('height', vb.height + 120);
    const revela = document.createElementNS(NS, 'path');
    revela.setAttribute('d', ruta.getAttribute('d'));
    revela.setAttribute('fill', 'none');
    revela.setAttribute('stroke', '#fff');
    revela.setAttribute('stroke-width', '30');
    revela.setAttribute('stroke-linecap', 'round');
    revela.setAttribute('stroke-linejoin', 'round');
    revela.setAttribute('stroke-dasharray', `${largo} ${largo * 2}`);
    mascara.appendChild(revela);
    defs.appendChild(mascara);
    ruta.setAttribute('mask', `url(#${idMascara})`);

    function fijar(p) {
      const d = Math.max(0, Math.min(1, p)) * largo;
      revela.setAttribute('stroke-dashoffset', String(largo - d));
      const a = ruta.getPointAtLength(Math.max(0, d - 0.6));
      const b = ruta.getPointAtLength(Math.min(largo, d + 0.6));
      const pt = ruta.getPointAtLength(d);
      const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
      avion.setAttribute('transform', `translate(${pt.x.toFixed(2)} ${pt.y.toFixed(2)}) rotate(${ang.toFixed(1)})`);
    }
    fijar(0);
    return fijar;
  }

  function volar(fijar) {
    if (reducirMovimiento) { fijar(1); return; }
    const duracion = 3400;
    let t0 = null;
    const paso = (ts) => {
      if (t0 === null) t0 = ts;
      const p = Math.min(1, (ts - t0) / duracion);
      fijar(ease(p));
      if (p < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  }

  function initIlustraciones() {
    $$('[data-svg]').forEach(async (caja) => {
      const svg = await cargarSvg(caja);
      if (!svg) return;
      const ruta = $('#ruta', svg);
      if (ruta) {
        let fijar = null;
        try { fijar = prepararRuta(svg); } catch (e) { console.warn('Ruta sin animar', e); } // primero se prepara (busca #ruta y #avion)…
        const sufijo = caja.className || 'x';
        ruta.id = 'ruta-' + sufijo;      // …y después se hacen únicos los ids (hay una ruta horizontal y otra vertical)
        ruta.classList.add('ruta__linea'); // el color terracota lo pone el CSS
        const avion = $('#avion', svg);
        if (avion) avion.id = 'avion-' + sufijo;
        if (!fijar) return;
        alEntrar(caja, () => volar(fijar), { threshold: 0.35 });
      } else {
        prepararTrazos(svg);
        alEntrar(caja, () => caja.classList.add('dibuja'), { threshold: 0.25 });
      }
    });
  }

  /* ---------- Copiar IBAN ---------- */
  function copiaAntigua(texto) {
    const ta = document.createElement('textarea');
    ta.value = texto;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, texto.length);
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    ta.remove();
    return ok;
  }

  function initCopiar() {
    $$('[data-copiar]').forEach((btn) => {
      const etiqueta = $('[data-copiar-txt]', btn);
      const original = etiqueta ? etiqueta.textContent : '';
      btn.addEventListener('click', async () => {
        const valor = btn.dataset.copiar.replace(/\s+/g, '');
        let ok = false;
        try { await navigator.clipboard.writeText(valor); ok = true; } catch (e) { ok = copiaAntigua(valor); }
        avisar(ok ? 'IBAN copiado ✓' : 'No hemos podido copiarlo: selecciona el número y cópialo a mano');
        if (ok && etiqueta) {
          btn.classList.add('copiado');
          etiqueta.textContent = '¡Copiado!';
          setTimeout(() => { btn.classList.remove('copiado'); etiqueta.textContent = original; }, 2200);
        }
      });
    });
  }

  /* ---------- Botón de contacto (solo si hay teléfono/correo configurado en #alojamiento) ---------- */
  function initContacto() {
    const sec = $('#alojamiento');
    const caja = sec && $('[data-contacto]', sec);
    if (!caja) return;
    const tel = (sec.dataset.whatsapp || '').replace(/\D+/g, '');
    const mail = (sec.dataset.email || '').trim();
    let a;
    if (tel) {
      a = document.createElement('a');
      a.href = `https://wa.me/${tel}?text=${encodeURIComponent('Hola Marta y Jorge, os escribo sobre el alojamiento para la boda.')}`;
      a.textContent = 'Escribirnos por WhatsApp';
    } else if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) {
      a = document.createElement('a');
      a.href = `mailto:${mail}?subject=${encodeURIComponent('Alojamiento para la boda')}`;
      a.textContent = 'Escribirnos un correo';
    }
    if (!a) return;
    a.className = 'boton';
    a.rel = 'noopener';
    if (tel) a.target = '_blank';
    caja.appendChild(a);
    caja.hidden = false;
  }

  /* ---------- Arranque ---------- */
  initFuentes();
  initRevelado();
  initCuenta();
  initIlustraciones();
  initCopiar();
  initContacto();
  // main.js ha arrancado: ya no hace falta el plan B que muestra todo pasados 4 s
  if (window.__revealTimer) clearTimeout(window.__revealTimer);
})();
