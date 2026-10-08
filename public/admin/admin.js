/* Panel de confirmaciones de Marta y Jorge (/admin). Sin dependencias.
   Pide la contraseña (ADMIN_TOKEN de Vercel), consulta /api/admin y muestra
   totales, alergias y respuestas. Los datos de los invitados se pintan SIEMPRE
   con textContent (nunca como HTML). La contraseña solo se recuerda en esta
   pestaña (sessionStorage) y viaja en la cabecera Authorization, nunca en la URL. */
(() => {
  'use strict';

  const CLAVE_SESION = 'mj-admin-token';
  const ETIQUETAS = {
    sin_gluten: 'Sin gluten / celiaquía', sin_lactosa: 'Sin lactosa', vegetariano: 'Vegetariano',
    vegano: 'Vegano', frutos_secos: 'Alergia a frutos secos', marisco: 'Alergia a marisco',
  };
  const $ = (s) => document.querySelector(s);
  const ui = {
    acceso: $('[data-acceso]'),
    formAcceso: $('[data-form-acceso]'),
    clave: $('#admin-clave'),
    errorAcceso: $('[data-error-acceso]'),
    entrar: $('[data-entrar]'),
    panel: $('[data-panel]'),
    actualizado: $('[data-actualizado]'),
    aviso: $('[data-aviso]'),
    alergias: $('[data-alergias]'),
    contador: $('[data-contador]'),
    vacio: $('[data-vacio]'),
    lista: $('[data-lista]'),
    buscar: $('[data-buscar]'),
    sustituidas: $('[data-sustituidas]'),
    recargar: $('[data-recargar]'),
    salir: $('[data-salir]'),
    notaPersonas: $('[data-kpi-nota-personas]'),
  };
  if (!ui.formAcceso || !ui.panel) return;

  let token = '';
  let datos = null;

  /* ---------- utilidades ---------- */
  const numero = (n) => Number(n || 0).toLocaleString('es-ES');
  const normalizar = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036F]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
  function el(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  function leerSesion() {
    try { return window.sessionStorage.getItem(CLAVE_SESION) || ''; } catch (e) { return ''; }
  }
  function guardarSesion(valor) {
    try {
      if (valor) window.sessionStorage.setItem(CLAVE_SESION, valor);
      else window.sessionStorage.removeItem(CLAVE_SESION);
    } catch (e) { /* sin almacenamiento: habrá que escribirla en cada visita */ }
  }
  const formatoFecha = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  const formatoCsv = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  function fechaCorta(iso) {
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? '' : formatoFecha.format(d);
  }
  function fechaCsv(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const p = {};
    formatoCsv.formatToParts(d).forEach((x) => { p[x.type] = x.value; });
    return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`;
  }

  /* ---------- datos de una respuesta ---------- */
  function nombrePersona(f, persona) {
    if (persona === 'titular') return f.nombre;
    const i = Number(String(persona).split('_')[1]) - 1;
    return (Array.isArray(f.acompanantes) && f.acompanantes[i] && f.acompanantes[i].nombre) || persona;
  }
  function alergiasDe(a) {
    return (Array.isArray(a.opciones) ? a.opciones : [])
      .map((o) => (ETIQUETAS[o] || o).toLowerCase())
      .concat(a.otras ? [a.otras] : [])
      .join(', ');
  }
  function alergiasTexto(f) {
    return (Array.isArray(f.alergias) ? f.alergias : [])
      .map((a) => `${a.nombre || nombrePersona(f, a.persona)}: ${alergiasDe(a)}`)
      .join(' · ');
  }
  const acompanantesTexto = (f) => (Array.isArray(f.acompanantes) ? f.acompanantes : []).map((a) => a.nombre).join(', ');

  /* ---------- petición ---------- */
  async function pedir(clave) {
    try {
      const r = await fetch('/api/admin', {
        headers: { Authorization: `Bearer ${encodeURIComponent(clave)}`, Accept: 'application/json' },
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
  function mensajeDeEstado(res) {
    if (res.status === 401) return 'Contraseña incorrecta.';
    if (res.status === 404) return 'El panel no está activado: falta ADMIN_TOKEN en Vercel (mínimo 12 caracteres) o hay que volver a desplegar.';
    if (res.status === 0) return 'No se ha podido conectar. Revisa la conexión e inténtalo de nuevo.';
    return (res.json && res.json.error) || 'Ha ocurrido un error inesperado. Inténtalo de nuevo en unos minutos.';
  }

  /* ---------- vistas ---------- */
  function mostrarAcceso(mensaje) {
    ui.panel.hidden = true;
    ui.acceso.hidden = false;
    ui.errorAcceso.textContent = mensaje || '';
    ui.clave.value = '';
    if (mensaje) ui.clave.setAttribute('aria-invalid', 'true'); else ui.clave.removeAttribute('aria-invalid');
    ui.clave.focus();
  }
  function mostrarPanel() {
    ui.acceso.hidden = true;
    ui.panel.hidden = false;
  }
  function avisar(texto) {
    ui.aviso.textContent = texto || '';
    ui.aviso.hidden = !texto;
  }

  function pintar(json) {
    datos = json;
    const r = json.resumen || {};
    document.querySelectorAll('[data-kpi]').forEach((n) => { n.textContent = numero(r[n.getAttribute('data-kpi')]); });
    if (ui.notaPersonas) {
      ui.notaPersonas.textContent = `${numero(r.confirman_si)} ${r.confirman_si === 1 ? 'respuesta' : 'respuestas'} + ${numero(r.acompanantes)} ${r.acompanantes === 1 ? 'acompañante' : 'acompañantes'}`;
    }
    ui.actualizado.textContent = `Actualizado ${fechaCorta(json.generado)} · ${numero(r.respuestas_recibidas)} ${r.respuestas_recibidas === 1 ? 'envío recibido' : 'envíos recibidos'}`;
    avisar(json.limite_alcanzado ? 'Se muestran las 1000 respuestas más recientes. Para verlas todas, usa el SQL Editor de Supabase (docs/rsvp.md).' : '');

    // Alergias (de quienes asisten, según su última respuesta)
    ui.alergias.textContent = '';
    const filas = Object.keys(ETIQUETAS).map((k) => [ETIQUETAS[k], (r.alergias || {})[k] || 0]);
    filas.push(['Otras (texto libre)', r.otras_alergias || 0]);
    filas.forEach(([etiqueta, n]) => {
      const tr = el('tr', n ? '' : 'cero');
      const th = el('th', '', etiqueta);
      th.scope = 'row';
      tr.append(th, el('td', '', numero(n)));
      ui.alergias.appendChild(tr);
    });
    pintarLista();
  }

  function filasVisibles() {
    if (!datos) return [];
    const filtro = (document.querySelector('input[name="filtro"]:checked') || {}).value || 'todas';
    const q = normalizar(ui.buscar.value);
    const verSustituidas = ui.sustituidas.checked;
    return datos.respuestas.filter((f) => (verSustituidas || f.vigente) &&
      (filtro === 'todas' || f.asistencia === filtro) &&
      (!q || normalizar(f.nombre).includes(q) || (f.acompanantes || []).some((a) => normalizar(a.nombre).includes(q))));
  }

  function tarjeta(f) {
    const si = f.asistencia === 'si';
    const li = el('li', `respuesta ${si ? 'respuesta--si' : 'respuesta--no'}${f.vigente ? '' : ' respuesta--sustituida'}`);
    const cab = el('div', 'respuesta__cabecera');
    cab.appendChild(el('span', 'respuesta__nombre', f.nombre));
    const personas = 1 + Number(f.n_acompanantes || 0);
    cab.appendChild(el('span', `respuesta__estado respuesta__estado--${si ? 'si' : 'no'}`,
      si ? `✓ Asiste${personas > 1 ? ` · ${personas} personas` : ''}` : '✗ No asiste'));
    const fecha = el('time', 'respuesta__fecha', fechaCorta(f.created_at));
    fecha.dateTime = f.created_at || '';
    cab.appendChild(fecha);
    li.appendChild(cab);

    const dl = el('dl', 'respuesta__datos');
    const fila = (titulo, valor, clase) => { dl.append(el('dt', '', titulo), el('dd', clase || '', valor)); };
    if (si && f.n_acompanantes > 0) fila('Acompañantes', acompanantesTexto(f));
    if (si && (f.transporte_ida || f.transporte_vuelta)) fila('Autocar', `${f.transporte_ida} ida · ${f.transporte_vuelta} vuelta`);
    if (si && Array.isArray(f.alergias) && f.alergias.length) fila('Alergias', alergiasTexto(f));
    if (f.mensaje) fila('Mensaje', f.mensaje, 'respuesta__mensaje');
    if (dl.children.length) li.appendChild(dl);

    if (!f.vigente) li.appendChild(el('p', 'respuesta__marca', 'Sustituida por una respuesta posterior con el mismo nombre'));
    else if (f.n_respuestas > 1) li.appendChild(el('p', 'respuesta__marca', `Ha respondido ${f.n_respuestas} veces: cuenta la última`));
    return li;
  }

  function pintarLista() {
    const filas = filasVisibles();
    ui.lista.textContent = '';
    const frag = document.createDocumentFragment();
    filas.forEach((f) => frag.appendChild(tarjeta(f)));
    ui.lista.appendChild(frag);
    const vigentes = datos ? datos.respuestas.filter((f) => f.vigente).length : 0;
    ui.contador.textContent = datos ? `${numero(filas.length)} de ${numero(vigentes)}` : '';
    if (!datos || !datos.respuestas.length) {
      ui.vacio.textContent = 'Todavía no hay ninguna respuesta. ¡Ya llegarán!';
      ui.vacio.hidden = false;
    } else if (!filas.length) {
      ui.vacio.textContent = 'Ninguna respuesta coincide con el filtro.';
      ui.vacio.hidden = false;
    } else {
      ui.vacio.hidden = true;
    }
  }

  /* ---------- CSV (separador «;» y BOM: se abre bien en Excel en español) ---------- */
  function celda(v) {
    if (v === null || v === undefined) return '';
    if (typeof v === 'number') return String(v);
    let s = String(v).replace(/\r\n?/g, '\n');
    // Evita que Excel/Sheets interprete el texto como fórmula (inyección CSV)
    if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
    return /[";\n]/.test(s) || /^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }
  function aCsv(filas) {
    return '\uFEFF' + filas.map((f) => f.map(celda).join(';')).join('\r\n') + '\r\n';
  }
  function descargar(nombre, texto) {
    const blob = new Blob([texto], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombre;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  }
  function csvRespuestas() {
    const incluirSustituidas = ui.sustituidas.checked;
    const filas = [['Fecha', 'Nombre', 'Asistencia', 'Personas', 'Acompañantes', 'Autocar ida', 'Autocar vuelta', 'Alergias', 'Mensaje', 'Veces que ha respondido', 'Estado']];
    datos.respuestas.filter((f) => incluirSustituidas || f.vigente).forEach((f) => {
      const si = f.asistencia === 'si';
      filas.push([fechaCsv(f.created_at), f.nombre, si ? 'Sí' : 'No', si ? 1 + Number(f.n_acompanantes || 0) : 0,
        acompanantesTexto(f), Number(f.transporte_ida || 0), Number(f.transporte_vuelta || 0), alergiasTexto(f),
        f.mensaje || '', Number(f.n_respuestas || 1), f.vigente ? 'Vigente' : 'Sustituida']);
    });
    return filas;
  }
  function csvPersonas() {
    const filas = [['Persona', 'Tipo', 'De parte de', 'Alergias e intolerancias']];
    datos.respuestas.filter((f) => f.vigente && f.asistencia === 'si').forEach((f) => {
      const alergiaDe = (clave) => {
        const a = (f.alergias || []).find((x) => x.persona === clave);
        return a ? alergiasDe(a) : '';
      };
      filas.push([f.nombre, 'Invitado/a', f.nombre, alergiaDe('titular')]);
      (f.acompanantes || []).forEach((a, i) => filas.push([a.nombre, 'Acompañante', f.nombre, alergiaDe(`acompanante_${i + 1}`)]));
    });
    return filas;
  }
  document.querySelectorAll('[data-csv]').forEach((boton) => {
    boton.addEventListener('click', () => {
      if (!datos) return;
      const tipo = boton.getAttribute('data-csv');
      const hoy = fechaCsv(new Date().toISOString()).slice(0, 10);
      if (tipo === 'personas') descargar(`boda-personas-${hoy}.csv`, aCsv(csvPersonas()));
      else descargar(`boda-confirmaciones-${hoy}.csv`, aCsv(csvRespuestas()));
    });
  });

  /* ---------- acciones ---------- */
  async function cargar() {
    ui.recargar.disabled = true;
    ui.actualizado.textContent = 'Cargando…';
    const res = await pedir(token);
    ui.recargar.disabled = false;
    if (res.status === 200 && res.json && res.json.ok) {
      pintar(res.json);
      return;
    }
    if (res.status === 401 || res.status === 404) {
      token = '';
      guardarSesion('');
      mostrarAcceso(mensajeDeEstado(res));
      return;
    }
    ui.actualizado.textContent = '';
    avisar(mensajeDeEstado(res));
  }

  ui.formAcceso.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const clave = ui.clave.value.trim();
    if (!clave) {
      ui.errorAcceso.textContent = 'Escribe la contraseña.';
      ui.clave.setAttribute('aria-invalid', 'true');
      ui.clave.focus();
      return;
    }
    ui.entrar.disabled = true;
    ui.entrar.textContent = 'Entrando…';
    ui.errorAcceso.textContent = '';
    const res = await pedir(clave);
    ui.entrar.disabled = false;
    ui.entrar.textContent = 'Entrar';
    if (res.status === 200 || res.status === 503) {
      // 503: la contraseña es buena pero la base de datos no responde; se muestra el diagnóstico.
      token = clave;
      guardarSesion(clave);
      mostrarPanel();
      if (res.status === 200 && res.json && res.json.ok) pintar(res.json);
      else { ui.actualizado.textContent = ''; avisar(mensajeDeEstado(res)); }
      ui.panel.setAttribute('tabindex', '-1');
      ui.panel.focus();
      return;
    }
    ui.clave.setAttribute('aria-invalid', 'true');
    ui.errorAcceso.textContent = mensajeDeEstado(res);
    ui.clave.select();
  });
  ui.clave.addEventListener('input', () => { ui.clave.removeAttribute('aria-invalid'); ui.errorAcceso.textContent = ''; });

  ui.recargar.addEventListener('click', cargar);
  ui.salir.addEventListener('click', () => {
    token = '';
    datos = null;
    guardarSesion('');
    ui.lista.textContent = '';
    mostrarAcceso('');
  });
  document.querySelectorAll('input[name="filtro"]').forEach((r) => r.addEventListener('change', pintarLista));
  ui.buscar.addEventListener('input', pintarLista);
  ui.sustituidas.addEventListener('change', pintarLista);

  /* ---------- arranque ---------- */
  token = leerSesion();
  if (token) { mostrarPanel(); cargar(); } else { mostrarAcceso(''); }
})();
