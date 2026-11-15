/* Panel de invitados de Marta y Jorge (/panel). Sin dependencias.
   · Acceso con correo y contraseña de Supabase Auth, siempre a través de /api/panel
     (el navegador nunca habla con Supabase ni ve la clave secreta).
   · La sesión (token de acceso + token de renovación) se guarda en localStorage si se marca
     «Mantener la sesión iniciada», o solo en esta pestaña (sessionStorage) si no.
   · Los datos de los invitados se pintan SIEMPRE con textContent (nunca como HTML). */
(() => {
  'use strict';

  const CLAVE = 'mj-panel-sesion';
  const BODA = Date.UTC(2027, 4, 8, 10); // 8 de mayo de 2027, 12:00 en Valladolid
  const RECARGA_MS = 5 * 60 * 1000;
  const ETIQUETAS = {
    sin_gluten: 'Sin gluten', sin_lactosa: 'Sin lactosa', vegetariano: 'Vegetariano',
    vegano: 'Vegano', frutos_secos: 'Frutos secos', marisco: 'Marisco',
  };

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const ui = {
    acceso: $('[data-vista="acceso"]'), panel: $('[data-vista="panel"]'),
    form: $('[data-form-acceso]'), email: $('[data-email]'), password: $('[data-password]'),
    verClave: $('[data-ver-clave]'), recordar: $('[data-recordar]'), entrar: $('[data-entrar]'), errorAcceso: $('[data-error-acceso]'),
    usuario: $('[data-usuario]'), cuentaAtras: $('[data-cuenta-atras]'), salir: $('[data-salir]'),
    contenido: $('#contenido'), actualizado: $('[data-actualizado]'), aviso: $('[data-aviso]'), recargar: $('[data-recargar]'),
    reparto: $('[data-reparto]'), grafica: $('[data-grafica]'), alergias: $('[data-alergias]'),
    filtros: $('[data-filtros]'), buscar: $('[data-buscar]'), sustituidas: $('[data-sustituidas]'),
    filas: $('[data-filas]'), vacio: $('[data-vacio]'), contador: $('[data-contador]'),
    fichaFondo: $('[data-ficha-fondo]'), ficha: $('[data-ficha]'), fichaEstado: $('[data-ficha-estado]'),
    fichaNombre: $('[data-ficha-nombre]'), fichaFecha: $('[data-ficha-fecha]'), fichaCuerpo: $('[data-ficha-cuerpo]'),
    cerrarFicha: $('[data-cerrar-ficha]'), tostada: $('[data-tostada]'),
  };
  if (!ui.form || !ui.panel) return;

  let sesion = null;   // { access_token, refresh_token, expires_at, recordar }
  let datos = null;    // respuesta de GET /api/panel
  let filtro = 'todos';
  let orden = { campo: 'fecha', dir: -1 };
  let temporizador = 0;
  let ultimoFoco = null;

  /* ---------- utilidades ---------- */
  const numero = (n) => Number(n || 0).toLocaleString('es-ES');
  const plural = (n, uno, varios) => `${numero(n)} ${n === 1 ? uno : varios}`;
  const normalizar = (s) => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  function el(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined && texto !== null) e.textContent = texto;
    return e;
  }
  function svg(etiqueta, attrs = {}) {
    const e = document.createElementNS('http://www.w3.org/2000/svg', etiqueta);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    return e;
  }
  const fmtFecha = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  const fmtLarga = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' });
  const fmtDia = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short' });
  const fmtClave = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit' });
  const fmtCsv = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  const fecha = (iso, f = fmtFecha) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? '' : f.format(d); };
  function fechaCsv(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const p = {};
    fmtCsv.formatToParts(d).forEach((x) => { p[x.type] = x.value; });
    return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`;
  }
  function haceCuanto(iso) {
    const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
    if (!Number.isFinite(s) || s < 45) return 'ahora mismo';
    const m = Math.round(s / 60);
    return m < 60 ? `hace ${m} min` : `a las ${fecha(iso, new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' }))}`;
  }
  let tTostada = 0;
  function tostada(texto) {
    ui.tostada.textContent = texto;
    ui.tostada.classList.add('tostada--visible');
    clearTimeout(tTostada);
    tTostada = setTimeout(() => ui.tostada.classList.remove('tostada--visible'), 2600);
  }

  /* ---------- datos de una respuesta ---------- */
  const personasDe = (f) => (f.asistencia === 'si' ? 1 + Number(f.n_acompanantes || 0) : 0);
  const acompanantes = (f) => (Array.isArray(f.acompanantes) ? f.acompanantes : []);
  const alergiasLista = (f) => (f.asistencia === 'si' && Array.isArray(f.alergias) ? f.alergias : []);
  function nombrePersona(f, persona) {
    if (persona === 'titular') return f.nombre;
    const i = Number(String(persona).split('_')[1]) - 1;
    return (acompanantes(f)[i] && acompanantes(f)[i].nombre) || persona;
  }
  function etiquetasAlergia(a) {
    return (Array.isArray(a.opciones) ? a.opciones : []).map((o) => ETIQUETAS[o] || o).concat(a.otras ? [a.otras] : []);
  }
  const alergiasTexto = (f) => alergiasLista(f).map((a) => `${a.nombre || nombrePersona(f, a.persona)}: ${etiquetasAlergia(a).join(', ').toLowerCase()}`).join(' · ');
  const tieneAutocar = (f) => f.asistencia === 'si' && (Number(f.transporte_ida) > 0 || Number(f.transporte_vuelta) > 0);

  /* ---------- sesión ---------- */
  function leerSesion() {
    for (const almacen of [window.localStorage, window.sessionStorage]) {
      try {
        const s = JSON.parse(almacen.getItem(CLAVE) || 'null');
        if (s && s.access_token && s.refresh_token) return s;
      } catch (e) { /* sin almacenamiento */ }
    }
    return null;
  }
  function guardarSesion(s) {
    sesion = s;
    for (const almacen of [window.localStorage, window.sessionStorage]) {
      try { almacen.removeItem(CLAVE); } catch (e) { /* nada */ }
    }
    if (!s) return;
    try { (s.recordar ? window.localStorage : window.sessionStorage).setItem(CLAVE, JSON.stringify(s)); } catch (e) { /* solo en memoria */ }
  }

  async function api(metodo, accion, { cuerpo, token } = {}) {
    try {
      const r = await fetch(`/api/panel${accion ? `?accion=${accion}` : ''}`, {
        method: metodo,
        headers: {
          Accept: 'application/json',
          ...(cuerpo ? { 'Content-Type': 'application/json' } : {}),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: cuerpo ? JSON.stringify(cuerpo) : undefined,
        cache: 'no-store',
        credentials: 'same-origin',
      });
      let json = null;
      try { json = await r.json(); } catch (e) { /* sin JSON */ }
      return { status: r.status, json };
    } catch (e) {
      return { status: 0, json: null };
    }
  }
  const mensaje = (res) => (res.status === 0
    ? 'No se ha podido conectar. Revisa la conexión e inténtalo de nuevo.'
    : (res.json && res.json.error) || 'Ha ocurrido un error inesperado. Inténtalo de nuevo en unos minutos.');

  async function renovar() {
    if (!sesion) return false;
    const res = await api('POST', 'renovar', { cuerpo: { refresh_token: sesion.refresh_token } });
    if (res.status === 200 && res.json && res.json.ok) {
      guardarSesion({ ...res.json.sesion, recordar: sesion.recordar });
      return true;
    }
    if (res.status === 401 || res.status === 403) {
      guardarSesion(null);
      mostrarAcceso(res.status === 403 ? mensaje(res) : 'La sesión ha caducado. Vuelve a entrar.');
    }
    return false;
  }

  /* ---------- vistas ---------- */
  function mostrarAcceso(texto) {
    clearInterval(temporizador);
    cerrarFicha();
    ui.panel.hidden = true;
    ui.acceso.hidden = false;
    ui.errorAcceso.textContent = texto || '';
    ui.password.value = '';
    (ui.email.value ? ui.password : ui.email).focus();
  }
  function mostrarPanel() {
    ui.acceso.hidden = true;
    ui.panel.hidden = false;
    pintarCuentaAtras();
    clearInterval(temporizador);
    temporizador = setInterval(() => { if (document.visibilityState === 'visible') cargar(true); }, RECARGA_MS);
  }
  function avisar(texto) {
    ui.aviso.textContent = texto || '';
    ui.aviso.hidden = !texto;
  }
  function pintarCuentaAtras() {
    const dias = Math.ceil((BODA - Date.now()) / 86400000);
    ui.cuentaAtras.textContent = dias > 1 ? `Faltan ${numero(dias)} días` : dias === 1 ? '¡Mañana es la boda!' : dias === 0 ? '¡Hoy es la boda!' : '¡Recién casados!';
  }

  async function cargar(silencioso = false) {
    if (!sesion) return mostrarAcceso('');
    if (!silencioso) { ui.recargar.disabled = true; ui.actualizado.textContent = 'Cargando…'; }
    if (sesion.expires_at && sesion.expires_at - 60 < Date.now() / 1000 && !(await renovar())) { ui.recargar.disabled = false; return; }
    let res = await api('GET', '', { token: sesion.access_token });
    if (res.status === 401 && (await renovar())) res = await api('GET', '', { token: sesion.access_token });
    ui.recargar.disabled = false;
    if (res.status === 200 && res.json && res.json.ok) {
      avisar(res.json.limite_alcanzado ? 'Se muestran las 1000 respuestas más recientes. Para verlas todas, usa el SQL Editor de Supabase (docs/rsvp.md).' : '');
      pintar(res.json);
      return;
    }
    if (res.status === 401 || res.status === 403) {
      guardarSesion(null);
      mostrarAcceso(res.status === 403 ? mensaje(res) : 'La sesión ha caducado. Vuelve a entrar.');
      return;
    }
    ui.actualizado.textContent = '';
    if (!silencioso) avisar(mensaje(res));
  }

  /* ---------- pintar ---------- */
  function pintar(json) {
    datos = json;
    const r = json.resumen || {};
    const u = json.usuario || {};
    ui.usuario.textContent = u.nombre ? `Hola, ${u.nombre}` : (u.email || '');
    $$('[data-kpi]').forEach((n) => { n.textContent = numero(r[n.getAttribute('data-kpi')]); });
    $('[data-nota="personas"]').textContent = `${plural(r.confirman_si, 'respuesta', 'respuestas')} + ${plural(r.acompanantes, 'acompañante', 'acompañantes')}`;
    $('[data-nota="respuestas"]').textContent = `${numero(r.confirman_si)} vienen · ${numero(r.no_asisten)} no pueden`;
    const total = (r.confirman_si || 0) + (r.no_asisten || 0);
    ui.reparto.firstElementChild.style.width = total ? `${(r.confirman_si / total) * 100}%` : '0';
    ui.reparto.lastElementChild.style.width = total ? `${(r.no_asisten / total) * 100}%` : '0';
    $('[data-nota="alergias"]').textContent = r.personas_con_alergias
      ? `El ${r.personas_asisten ? Math.round((r.personas_con_alergias / r.personas_asisten) * 100) : 0}% de los que vienen`
      : 'Nadie ha indicado alergias';
    ui.actualizado.textContent = `Actualizado ${haceCuanto(json.generado)} · ${plural(r.respuestas_recibidas, 'envío recibido', 'envíos recibidos')}`;
    pintarGrafica();
    pintarAlergias(r);
    pintarTabla();
  }

  function pintarGrafica() {
    ui.grafica.textContent = '';
    const si = datos.respuestas.filter((f) => f.vigente && f.asistencia === 'si').sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    if (!si.length) {
      ui.grafica.appendChild(el('p', 'grafica__vacia', 'Aquí verás cómo crecen las confirmaciones en cuanto lleguen las primeras.'));
      return;
    }
    // personas acumuladas por día (hora de España), desde el primer día con respuesta hasta hoy
    const porDia = new Map();
    si.forEach((f) => { const k = fmtClave.format(new Date(f.created_at)); porDia.set(k, (porDia.get(k) || 0) + personasDe(f)); });
    const dias = [];
    const inicio = new Date(`${fmtClave.format(new Date(si[0].created_at))}T12:00:00Z`);
    const hoy = fmtClave.format(new Date());
    for (let d = new Date(inicio), acum = 0; ; d.setUTCDate(d.getUTCDate() + 1)) {
      const k = d.toISOString().slice(0, 10);
      acum += porDia.get(k) || 0;
      dias.push({ k, acum, fecha: new Date(d) });
      if (k >= hoy || dias.length > 800) break;
    }
    if (dias.length === 1) dias.unshift({ k: '', acum: 0, fecha: new Date(inicio.getTime() - 86400000) });

    // a tamaño real (sin estirar): el texto de los ejes no se deforma
    const W = Math.max(280, ui.grafica.clientWidth || 640);
    const H = window.matchMedia('(min-width: 900px)').matches ? 296 : 208;
    const m = { t: 14, r: 12, b: 26, l: 34 };
    const max = Math.max(4, ...dias.map((d) => d.acum));
    const paso = Math.pow(10, Math.floor(Math.log10(max))) * (max / Math.pow(10, Math.floor(Math.log10(max))) > 5 ? 2 : 1);
    const techo = Math.ceil(max / paso) * paso;
    const x = (i) => m.l + (i / (dias.length - 1)) * (W - m.l - m.r);
    const y = (v) => H - m.b - (v / techo) * (H - m.t - m.b);
    const s = svg('svg', { viewBox: `0 0 ${W} ${H}`, 'aria-hidden': 'true' });
    const defs = svg('defs');
    const grad = svg('linearGradient', { id: 'relleno-grafica', x1: '0', y1: '0', x2: '0', y2: '1' });
    grad.append(svg('stop', { offset: '0%', 'stop-color': '#b23a40', 'stop-opacity': '.22' }), svg('stop', { offset: '100%', 'stop-color': '#b23a40', 'stop-opacity': '0' }));
    defs.appendChild(grad);
    s.appendChild(defs);
    for (let v = 0; v <= techo; v += paso) {
      s.appendChild(svg('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), stroke: '#ece6df', 'stroke-width': '1' }));
      const t = svg('text', { x: m.l - 8, y: y(v) + 4, 'text-anchor': 'end' });
      t.textContent = numero(v);
      s.appendChild(t);
    }
    // escalones: la línea sube el día que llega una confirmación
    let d = `M${x(0)} ${y(dias[0].acum)}`;
    dias.forEach((p, i) => { if (i) d += `H${x(i)}V${y(p.acum)}`; });
    s.appendChild(svg('path', { d: `${d}V${y(0)}H${x(0)}Z`, fill: 'url(#relleno-grafica)', stroke: 'none' }));
    s.appendChild(svg('path', { d, stroke: '#b23a40', 'stroke-width': '2.2', fill: 'none' }));
    const marcas = Math.min(5, dias.length);
    for (let i = 0; i < marcas; i++) {
      const j = Math.round((i / Math.max(1, marcas - 1)) * (dias.length - 1));
      const t = svg('text', { x: x(j), y: H - 6, 'text-anchor': i === 0 ? 'start' : i === marcas - 1 ? 'end' : 'middle' });
      t.textContent = fmtDia.format(dias[j].fecha);
      s.appendChild(t);
    }
    const ult = dias[dias.length - 1];
    s.appendChild(svg('circle', { cx: x(dias.length - 1), cy: y(ult.acum), r: '4', fill: '#b23a40', stroke: '#fff', 'stroke-width': '2' }));
    ui.grafica.setAttribute('aria-label', `Evolución de las confirmaciones: ${plural(ult.acum, 'persona', 'personas')} a día de hoy`);
    ui.grafica.appendChild(s);
  }

  function pintarAlergias(r) {
    ui.alergias.textContent = '';
    const filas = Object.keys(ETIQUETAS).map((k) => [ETIQUETAS[k], (r.alergias || {})[k] || 0]);
    filas.push(['Otras (texto libre)', r.otras_alergias || 0]);
    const max = Math.max(1, ...filas.map((f) => f[1]));
    filas.sort((a, b) => b[1] - a[1]).forEach(([etiqueta, n]) => {
      const li = el('li', n ? '' : 'cero');
      li.append(el('span', '', etiqueta), el('span', 'barras__n', numero(n)));
      const pista = el('span', 'barras__pista');
      const relleno = el('span', 'barras__relleno');
      relleno.style.width = `${(n / max) * 100}%`;
      pista.appendChild(relleno);
      li.appendChild(pista);
      ui.alergias.appendChild(li);
    });
  }

  /* ---------- tabla ---------- */
  const FILTROS = {
    todos: () => true,
    si: (f) => f.asistencia === 'si',
    no: (f) => f.asistencia === 'no',
    alergias: (f) => alergiasLista(f).length > 0,
    autocar: tieneAutocar,
    mensaje: (f) => Boolean(String(f.mensaje || '').trim()),
  };
  function base() {
    return datos ? datos.respuestas.filter((f) => ui.sustituidas.checked || f.vigente) : [];
  }
  function filasVisibles() {
    const q = normalizar(ui.buscar.value);
    const lista = base().filter((f) => FILTROS[filtro](f) &&
      (!q || normalizar(f.nombre).includes(q) || acompanantes(f).some((a) => normalizar(a.nombre).includes(q))));
    const clave = {
      nombre: (f) => normalizar(f.nombre),
      personas: (f) => personasDe(f),
      fecha: (f) => new Date(f.created_at).getTime() || 0,
    }[orden.campo];
    return lista.sort((a, b) => (clave(a) < clave(b) ? -1 : clave(a) > clave(b) ? 1 : 0) * orden.dir);
  }
  function celda(fila, col, clase) {
    const td = el('td', clase || '');
    td.setAttribute('data-col', col);
    fila.appendChild(td);
    return td;
  }
  function pintarTabla() {
    const visibles = filasVisibles();
    ui.filas.textContent = '';
    const frag = document.createDocumentFragment();
    visibles.forEach((f) => {
      const tr = el('tr', f.vigente ? '' : 'sustituida');
      tr.tabIndex = 0;
      tr.setAttribute('aria-label', `${f.nombre}: ver detalle`);
      tr.addEventListener('click', () => abrirFicha(f, tr));
      tr.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrirFicha(f, tr); } });

      const nombre = celda(tr, 'Invitado');
      nombre.removeAttribute('data-col');
      nombre.append(el('span', 'invitado__nombre', f.nombre));
      const acomp = acompanantes(f).map((a) => a.nombre).join(', ');
      if (f.asistencia === 'si' && acomp) nombre.append(el('span', 'invitado__sub', `con ${acomp}`));

      const estado = celda(tr, 'Estado');
      if (!f.vigente) estado.append(el('span', 'etiqueta etiqueta--vieja', 'Sustituida'));
      else estado.append(el('span', `etiqueta etiqueta--${f.asistencia === 'si' ? 'si' : 'no'}`, f.asistencia === 'si' ? 'Viene' : 'No viene'));

      const personas = celda(tr, 'Personas', 'num');
      personas.textContent = f.asistencia === 'si' ? numero(personasDe(f)) : '—';
      if (f.asistencia !== 'si') { personas.classList.add('guion', 'vacia-movil'); }

      const bus = celda(tr, 'Autocar');
      if (tieneAutocar(f)) {
        const c = el('span', 'chips');
        if (Number(f.transporte_ida) > 0) c.append(el('span', 'etiqueta etiqueta--bus', `Ida ${f.transporte_ida}`));
        if (Number(f.transporte_vuelta) > 0) c.append(el('span', 'etiqueta etiqueta--bus', `Vuelta ${f.transporte_vuelta}`));
        bus.append(c);
      } else { bus.append(el('span', 'guion', '—')); bus.classList.add('vacia-movil'); }

      const al = celda(tr, 'Alergias');
      const etiquetas = [...new Set(alergiasLista(f).flatMap(etiquetasAlergia))];
      if (etiquetas.length) {
        const c = el('span', 'chips');
        etiquetas.slice(0, 3).forEach((t) => c.append(el('span', 'etiqueta etiqueta--alergia', t)));
        if (etiquetas.length > 3) c.append(el('span', 'etiqueta etiqueta--vieja', `+${etiquetas.length - 3}`));
        al.append(c);
      } else { al.append(el('span', 'guion', '—')); al.classList.add('vacia-movil'); }

      const msj = celda(tr, 'Mensaje', 'centro');
      if (String(f.mensaje || '').trim()) {
        const i = svg('svg', { class: 'icono-mensaje', viewBox: '0 0 20 20', role: 'img', 'aria-label': 'Tiene mensaje' });
        i.appendChild(svg('path', { d: 'M4 4.5h12a1 1 0 0 1 1 1v7.5a1 1 0 0 1-1 1H8l-4 3v-3a1 1 0 0 1-1-1V5.5a1 1 0 0 1 1-1z' }));
        msj.append(i);
      } else { msj.append(el('span', 'guion', '—')); msj.classList.add('vacia-movil'); }

      const fch = celda(tr, 'Fecha', 'num');
      const t = el('time', '', fecha(f.created_at));
      t.dateTime = f.created_at || '';
      fch.append(t);
      frag.appendChild(tr);
    });
    ui.filas.appendChild(frag);

    // contadores de los filtros (sobre lo que se ve, sin el buscador)
    const b = base();
    $$('button[data-filtro]', ui.filtros).forEach((boton) => {
      boton.querySelector('span').textContent = numero(b.filter(FILTROS[boton.getAttribute('data-filtro')]).length);
    });
    const vacio = !datos || !datos.respuestas.length;
    ui.vacio.hidden = visibles.length > 0;
    ui.vacio.textContent = vacio ? 'Todavía no ha respondido nadie. ¡Ya llegarán!' : 'Ningún invitado coincide con la búsqueda o el filtro.';
    const personas = visibles.reduce((s, f) => s + (f.vigente ? personasDe(f) : 0), 0);
    ui.contador.textContent = datos ? `${plural(visibles.length, 'respuesta', 'respuestas')} · ${plural(personas, 'persona que viene', 'personas que vienen')}` : '';
  }

  /* ---------- ficha de un invitado ---------- */
  function abrirFicha(f, origen) {
    ultimoFoco = origen || document.activeElement;
    const si = f.asistencia === 'si';
    ui.fichaEstado.textContent = '';
    ui.fichaEstado.append(el('span', `etiqueta etiqueta--${f.vigente ? (si ? 'si' : 'no') : 'vieja'}`, f.vigente ? (si ? 'Viene' : 'No viene') : 'Respuesta sustituida'));
    ui.fichaNombre.textContent = f.nombre;
    ui.fichaFecha.textContent = `Respondió el ${fecha(f.created_at, fmtLarga)}`;
    const cuerpo = ui.fichaCuerpo;
    cuerpo.textContent = '';
    const bloque = (titulo) => { const b = el('section', 'ficha__bloque'); b.append(el('h3', '', titulo)); cuerpo.append(b); return b; };

    if (!f.vigente) cuerpo.append(el('p', 'ficha__nota', 'Esta persona respondió otra vez más tarde: cuenta su última respuesta.'));
    else if (f.n_respuestas > 1) cuerpo.append(el('p', 'ficha__nota', `Ha respondido ${f.n_respuestas} veces: esta es la última, la que cuenta.`));

    if (si) {
      const lista = el('ul', 'ficha__personas');
      const persona = (nombre, tipo, clave) => {
        const li = el('li');
        li.append(el('strong', '', nombre));
        const a = alergiasLista(f).find((x) => x.persona === clave);
        li.append(el('span', '', a ? `${tipo} · ${etiquetasAlergia(a).join(', ')}` : `${tipo} · sin alergias`));
        lista.append(li);
      };
      persona(f.nombre, 'Invitado/a', 'titular');
      acompanantes(f).forEach((a, i) => persona(a.nombre, 'Acompañante', `acompanante_${i + 1}`));
      bloque(`${plural(personasDe(f), 'persona', 'personas')}`).append(lista);

      const bus = el('div', 'ficha__dato');
      const dato = (n, t) => { const p = el('p'); p.append(el('strong', '', numero(n)), el('span', '', t)); bus.append(p); };
      dato(f.transporte_ida, 'plazas de ida (San Pablo → Posada)');
      dato(f.transporte_vuelta, 'plazas de vuelta (Posada → Poniente)');
      bloque('Autocar').append(bus);
    }
    if (String(f.mensaje || '').trim()) bloque('Su mensaje').append(el('blockquote', 'ficha__mensaje', f.mensaje));

    ui.fichaFondo.hidden = false;
    ui.ficha.hidden = false;
    document.body.style.overflow = 'hidden';
    ui.ficha.focus();
  }
  function cerrarFicha() {
    if (ui.ficha.hidden) return;
    ui.ficha.hidden = true;
    ui.fichaFondo.hidden = true;
    document.body.style.overflow = '';
    if (ultimoFoco && ultimoFoco.focus) ultimoFoco.focus();
  }
  ui.cerrarFicha.addEventListener('click', cerrarFicha);
  ui.fichaFondo.addEventListener('click', cerrarFicha);
  document.addEventListener('keydown', (e) => {
    if (ui.ficha.hidden) return;
    if (e.key === 'Escape') { cerrarFicha(); return; }
    if (e.key === 'Tab') { // el foco no sale de la ficha
      const enfocables = $$('button, [href], [tabindex]:not([tabindex="-1"])', ui.ficha);
      if (!enfocables.length) { e.preventDefault(); return; }
      const [primero, ultimo] = [enfocables[0], enfocables[enfocables.length - 1]];
      if (e.shiftKey && document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
      else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
    }
  });

  /* ---------- CSV (separador «;» y BOM: se abre bien en Excel en español) ---------- */
  function celdaCsv(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return String(v);
    let s = String(v).replace(/\r\n?/g, '\n');
    if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`; // evita que Excel/Sheets lo tome por una fórmula
    return /[";\n]/.test(s) || /^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }
  const aCsv = (filas) => '﻿' + filas.map((f) => f.map(celdaCsv).join(';')).join('\r\n') + '\r\n';
  function descargar(nombre, texto) {
    const url = URL.createObjectURL(new Blob([texto], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }
  function csvRespuestas() {
    const filas = [['Fecha', 'Nombre', 'Asistencia', 'Personas', 'Acompañantes', 'Autocar ida', 'Autocar vuelta', 'Alergias', 'Mensaje', 'Veces que ha respondido', 'Estado']];
    base().forEach((f) => {
      const si = f.asistencia === 'si';
      filas.push([fechaCsv(f.created_at), f.nombre, si ? 'Sí' : 'No', personasDe(f), acompanantes(f).map((a) => a.nombre).join(', '),
        Number(f.transporte_ida || 0), Number(f.transporte_vuelta || 0), alergiasTexto(f), f.mensaje || '',
        Number(f.n_respuestas || 1), f.vigente ? 'Vigente' : 'Sustituida']);
    });
    return filas;
  }
  function csvPersonas() {
    const filas = [['Persona', 'Tipo', 'De parte de', 'Alergias e intolerancias']];
    datos.respuestas.filter((f) => f.vigente && f.asistencia === 'si').forEach((f) => {
      const de = (clave) => { const a = alergiasLista(f).find((x) => x.persona === clave); return a ? etiquetasAlergia(a).join(', ').toLowerCase() : ''; };
      filas.push([f.nombre, 'Invitado/a', f.nombre, de('titular')]);
      acompanantes(f).forEach((a, i) => filas.push([a.nombre, 'Acompañante', f.nombre, de(`acompanante_${i + 1}`)]));
    });
    return filas;
  }
  $$('[data-csv]').forEach((boton) => boton.addEventListener('click', () => {
    if (!datos) return;
    const hoy = fechaCsv(new Date().toISOString()).slice(0, 10);
    if (boton.getAttribute('data-csv') === 'personas') descargar(`boda-personas-${hoy}.csv`, aCsv(csvPersonas()));
    else descargar(`boda-confirmaciones-${hoy}.csv`, aCsv(csvRespuestas()));
    tostada('Descargado. Se abre con Excel o Google Sheets.');
  }));

  /* ---------- eventos ---------- */
  ui.form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const email = ui.email.value.trim();
    const password = ui.password.value;
    ui.email.removeAttribute('aria-invalid');
    ui.password.removeAttribute('aria-invalid');
    if (!email || !password) {
      ui.errorAcceso.textContent = !email ? 'Escribe tu correo.' : 'Escribe la contraseña.';
      (!email ? ui.email : ui.password).setAttribute('aria-invalid', 'true');
      (!email ? ui.email : ui.password).focus();
      return;
    }
    ui.entrar.disabled = true;
    ui.entrar.textContent = 'Entrando…';
    ui.errorAcceso.textContent = '';
    const res = await api('POST', 'entrar', { cuerpo: { email, password } });
    ui.entrar.disabled = false;
    ui.entrar.textContent = 'Entrar';
    if (res.status === 200 && res.json && res.json.ok) {
      guardarSesion({ ...res.json.sesion, recordar: ui.recordar.checked });
      ui.password.value = '';
      mostrarPanel();
      ui.contenido.focus();
      cargar();
      return;
    }
    ui.errorAcceso.textContent = mensaje(res);
    if (res.status === 401) { ui.password.setAttribute('aria-invalid', 'true'); ui.password.select(); }
  });
  ui.verClave.addEventListener('click', () => {
    const ver = ui.password.type === 'password';
    ui.password.type = ver ? 'text' : 'password';
    ui.verClave.textContent = ver ? 'Ocultar' : 'Ver';
    ui.verClave.setAttribute('aria-pressed', String(ver));
    ui.verClave.setAttribute('aria-label', ver ? 'Ocultar la contraseña' : 'Mostrar la contraseña');
  });
  ui.recargar.addEventListener('click', async () => { await cargar(); if (datos) tostada('Datos actualizados'); });
  ui.salir.addEventListener('click', async () => {
    const token = sesion && sesion.access_token;
    guardarSesion(null);
    datos = null;
    ui.filas.textContent = '';
    mostrarAcceso('');
    if (token) api('POST', 'salir', { token });
  });
  ui.filtros.addEventListener('click', (e) => {
    const boton = e.target.closest('button[data-filtro]');
    if (!boton) return;
    filtro = boton.getAttribute('data-filtro');
    $$('button[data-filtro]', ui.filtros).forEach((b) => b.setAttribute('aria-selected', String(b === boton)));
    pintarTabla();
  });
  $$('button[data-orden]').forEach((boton) => boton.addEventListener('click', () => {
    const campo = boton.getAttribute('data-orden');
    orden = { campo, dir: orden.campo === campo ? -orden.dir : (campo === 'nombre' ? 1 : -1) };
    $$('button[data-orden]').forEach((b) => b.removeAttribute('aria-sort'));
    boton.setAttribute('aria-sort', orden.dir === 1 ? 'ascending' : 'descending');
    pintarTabla();
  }));
  ui.buscar.addEventListener('input', pintarTabla);
  ui.sustituidas.addEventListener('change', pintarTabla);
  let tRedim = 0;
  window.addEventListener('resize', () => { clearTimeout(tRedim); tRedim = setTimeout(() => { if (datos && !ui.panel.hidden) pintarGrafica(); }, 150); });
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && sesion && !ui.panel.hidden && datos && Date.now() - new Date(datos.generado).getTime() > 60000) cargar(true);
  });

  /* ---------- arranque ---------- */
  sesion = leerSesion();
  if (sesion) { mostrarPanel(); cargar(); } else { mostrarAcceso(''); }
})();
