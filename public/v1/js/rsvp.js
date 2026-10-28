/* ==========================================================================
   Marta & Jorge · formulario de confirmación de asistencia (RSVP)
   Vanilla ES2020, sin dependencias. Mejora progresiva: sin JavaScript el botón
   queda desactivado y el <noscript> lo explica.
   · Despliega acompañantes, autocar y alergias solo si la respuesta es «Sí».
   · Valida en el navegador (el servidor vuelve a validarlo todo).
   · Envía JSON a /api/rsvp con un submission_id (idempotente) y un único
     reintento si falla la red. Guarda un borrador en localStorage por si se
     recarga la página, y lo borra al enviar.
   Documentación: docs/rsvp.md
   ========================================================================== */
(() => {
  'use strict';

  const raiz = document.querySelector('[data-rsvp]');
  const form = raiz && raiz.querySelector('[data-rsvp-form]');
  if (!form) return;

  /* ---------- Textos (todos en un sitio para poder retocarlos) ---------- */
  const TXT = {
    nombreVacio: 'Escribe tu nombre y apellidos.',
    nombreNoValido: 'Escribe un nombre válido.',
    nombreLargo: 'Es demasiado largo (máximo 120 caracteres).',
    acompananteVacio: 'Escribe su nombre y apellidos.', // va justo debajo de «…del acompañante N»
    asistencia: 'Indica si podrás asistir.',
    enviar: 'Enviar confirmación',
    enviando: 'Enviando…',
    errorTitulo: 'No hemos podido enviar tu respuesta.',
    errorTexto: 'Inténtalo de nuevo en unos minutos o escríbenos. No se pierde nada de lo que has escrito.',
    sinConexionTitulo: 'Parece que no tienes conexión.',
    sinConexionTexto: 'Revisa tu conexión a internet y vuelve a pulsar «Enviar confirmación». No se pierde nada de lo que has escrito.',
    conexionVuelve: 'Ya tienes conexión de nuevo: pulsa «Enviar confirmación».',
    whatsapp: 'Envíanosla por WhatsApp',
    correo: 'Envíanosla por correo',
  };
  const ETIQUETAS_ALERGIA = {
    sin_gluten: 'sin gluten / celiaquía', sin_lactosa: 'sin lactosa', vegetariano: 'vegetariano',
    vegano: 'vegano', frutos_secos: 'alergia a frutos secos', marisco: 'alergia a marisco',
  };

  /* ---------- Constantes ---------- */
  const ENDPOINT = raiz.getAttribute('data-endpoint') || '/api/rsvp';
  const CLAVE_BORRADOR = 'mj-rsvp-borrador-v1';
  const CADUCIDAD_BORRADOR = 60 * 24 * 3600 * 1000; // 60 días
  const MAX_ACOMPANANTES = 8;
  const MAX_PLAZAS = 9;
  const ESPERA_MINIMA = 2600;    // el servidor rechaza envíos hechos en menos de 2,5 s
  const LIMITE_PETICION = 15000; // ms por intento
  const RE_UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const RE_LETRA = (() => {
    try { return new RegExp('\\p{L}', 'u'); } catch (e) { return /[A-Za-zÀ-ÖØ-öø-ÿ]/; }
  })();
  const RE_INVISIBLES = /[\u200B\u200E\u200F\u202A-\u202E\u2060-\u2064\u2066-\u2069\uFEFF]/g;
  const RE_CONTROL = /[\u0000-\u001F\u007F-\u009F]/g;
  const reducirMovimiento = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const inicio = performance.now();

  /* ---------- Elementos ---------- */
  const $ = (sel, ctx = form) => ctx.querySelector(sel);
  const $$ = (sel, ctx = form) => Array.from(ctx.querySelectorAll(sel));
  const ui = {
    nombre: $('#rsvp-nombre'),
    radios: $$('input[name="asistencia"]'),
    detalles: $('[data-rsvp-detalles]'),
    n: $('#rsvp-n'),
    ida: $('#rsvp-ida'),
    vuelta: $('#rsvp-vuelta'),
    listaAcompanantes: $('[data-rsvp-lista-acompanantes]'),
    listaPersonas: $('[data-rsvp-lista-personas]'),
    mensaje: $('#rsvp-mensaje'),
    cuenta: $('[data-rsvp-cuenta]'),
    trampa: $('#rsvp-hp'),
    aviso: $('[data-rsvp-aviso]'),
    enviar: $('[data-rsvp-enviar]'),
    enviarTexto: $('[data-rsvp-enviar-texto]'),
    anuncio: $('[data-rsvp-anuncio]'),
    recuperado: $('[data-rsvp-recuperado]'),
    vaciar: $('[data-rsvp-vaciar]'),
    tplAcompanante: $('#rsvp-tpl-acompanante'),
    tplPersona: $('#rsvp-tpl-persona'),
    gracias: raiz.querySelector('[data-rsvp-gracias]'),
    graciasTitulo: raiz.querySelector('[data-rsvp-gracias-titulo]'),
    graciasTexto: raiz.querySelector('[data-rsvp-gracias-texto]'),
    graciasResumen: raiz.querySelector('[data-rsvp-gracias-resumen]'),
    modificar: raiz.querySelector('[data-rsvp-modificar]'),
  };
  if (!ui.nombre || !ui.n || !ui.ida || !ui.vuelta || !ui.mensaje || !ui.enviar || !ui.aviso ||
      !ui.tplAcompanante || !ui.tplPersona || !ui.gracias || !ui.detalles) return;

  /* ---------- Estado ---------- */
  const estado = {
    n: 0,
    acompanantes: [],        // [{ envoltorio, input, error, numero }]
    personas: new Map(),     // 'titular' | 'acompanante_N' → { envoltorio, titulo, casillas, otras, error, numero }
    errores: new Map(),      // clave de error → destino
    submissionId: nuevoId(),
    intento: null,           // { id, firma } del último envío sin confirmar (para no duplicar)
    enviando: false,
    avisoSinConexion: false,
    avisoLimite: false,
  };

  /* ---------- Utilidades ---------- */
  function nuevoId() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') return window.crypto.randomUUID();
    } catch (e) { /* contexto no seguro */ }
    const b = new Uint8Array(16);
    if (window.crypto && window.crypto.getRandomValues) window.crypto.getRandomValues(b);
    else for (let i = 0; i < 16; i++) b[i] = Math.floor(Math.random() * 256);
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    const h = Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
    return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
  }
  const pausa = (ms) => new Promise((r) => setTimeout(r, ms));
  const limitar = (v, min, max) => Math.min(max, Math.max(min, v));

  /** Igual que en el servidor: sin invisibles ni controles, espacios colapsados. */
  function limpiar(texto) {
    let t = String(texto == null ? '' : texto);
    if (typeof t.normalize === 'function') t = t.normalize('NFC');
    return t.replace(RE_INVISIBLES, '').replace(RE_CONTROL, ' ').replace(/\s+/g, ' ').trim();
  }

  let relojAnuncio;
  function anunciar(texto) {
    if (!ui.anuncio) return;
    ui.anuncio.textContent = '';
    clearTimeout(relojAnuncio);
    relojAnuncio = setTimeout(() => { ui.anuncio.textContent = texto; }, 80);
  }

  function desplazarA(elemento, bloque = 'center') {
    if (!elemento || typeof elemento.scrollIntoView !== 'function') return;
    try { elemento.scrollIntoView({ behavior: reducirMovimiento ? 'auto' : 'smooth', block: bloque }); }
    catch (e) { elemento.scrollIntoView(); }
  }
  function enfocar(elemento, bloque = 'center') {
    if (!elemento) return;
    try { elemento.focus({ preventScroll: true }); } catch (e) { elemento.focus(); }
    desplazarA(elemento, bloque);
  }

  /** Abre o cierra un bloque plegable (y lo hace inerte mientras está cerrado). */
  function plegar(envoltorio, abrir) {
    if (!envoltorio) return;
    envoltorio.classList.toggle('abierto', !!abrir);
    if ('inert' in envoltorio) envoltorio.inert = !abrir;
  }

  /* ---------- Acompañantes y tarjetas de alergias ---------- */
  // En móvil el ejemplo largo de «Otras alergias» no cabe: se usa uno corto.
  const pantallaEstrecha = window.matchMedia ? window.matchMedia('(max-width: 559px)') : null;
  function ponerEjemplo(input) {
    if (!input.hasAttribute('data-placeholder-largo')) input.setAttribute('data-placeholder-largo', input.placeholder);
    const corto = input.getAttribute('data-placeholder-corto');
    input.placeholder = pantallaEstrecha && pantallaEstrecha.matches && corto ? corto : input.getAttribute('data-placeholder-largo');
  }
  if (pantallaEstrecha) {
    const alCambiar = () => estado.personas.forEach((p) => ponerEjemplo(p.otras));
    if (pantallaEstrecha.addEventListener) pantallaEstrecha.addEventListener('change', alCambiar);
    else if (pantallaEstrecha.addListener) pantallaEstrecha.addListener(alCambiar);
  }

  function crearPersona(clave, numero) {
    const frag = ui.tplPersona.content.cloneNode(true);
    const envoltorio = frag.querySelector('[data-persona]');
    const titulo = frag.querySelector('[data-ref="titulo"]');
    const otras = frag.querySelector('[data-ref="otras"]');
    const otrasEtiqueta = frag.querySelector('[data-ref="otras-etiqueta"]');
    const error = frag.querySelector('[data-ref="error"]');
    const casillas = Array.from(frag.querySelectorAll('input[type="checkbox"]'));
    const base = `rsvp-alergias-${clave}`;
    casillas.forEach((c) => { c.name = `${base}-opciones`; });
    otras.id = `${base}-otras`;
    otras.name = `${base}-otras`;
    otrasEtiqueta.htmlFor = otras.id;
    error.id = `${base}-error`;
    otras.setAttribute('aria-describedby', error.id);
    ponerEjemplo(otras);
    envoltorio.setAttribute('data-persona', clave);
    titulo.textContent = clave === 'titular' ? 'Tú' : `Acompañante ${numero}`;
    plegar(envoltorio, clave === 'titular');
    ui.listaPersonas.appendChild(frag);
    estado.personas.set(clave, { envoltorio, titulo, casillas, otras, error, numero });
  }

  function crearAcompanante(numero) {
    const frag = ui.tplAcompanante.content.cloneNode(true);
    const envoltorio = frag.querySelector('[data-acompanante]');
    const etiqueta = frag.querySelector('[data-ref="etiqueta"]');
    const input = frag.querySelector('[data-ref="nombre"]');
    const error = frag.querySelector('[data-ref="error"]');
    frag.querySelector('[data-ref="numero"]').textContent = String(numero);
    input.id = `rsvp-acompanante-${numero}`;
    input.name = `acompanante_${numero}`;
    etiqueta.htmlFor = input.id;
    error.id = `${input.id}-error`;
    input.setAttribute('aria-describedby', error.id);
    plegar(envoltorio, false);
    ui.listaAcompanantes.appendChild(frag);
    estado.acompanantes.push({ envoltorio, input, error, numero });
    input.addEventListener('input', () => {
      ponerTituloPersona(numero);
      revalidarNombre(input, `acompanantes.${numero - 1}.nombre`, TXT.acompananteVacio);
    });
    crearPersona(`acompanante_${numero}`, numero);
  }

  function ponerTituloPersona(numero) {
    const p = estado.personas.get(`acompanante_${numero}`);
    const slot = estado.acompanantes[numero - 1];
    if (p && slot) p.titulo.textContent = limpiar(slot.input.value) || `Acompañante ${numero}`;
  }

  /** Muestra n campos de acompañante (conserva lo escrito en los que se ocultan). */
  function fijarAcompanantes(n, { anunciarCambio = false } = {}) {
    n = limitar(Number.isFinite(n) ? Math.round(n) : 0, 0, MAX_ACOMPANANTES);
    estado.n = n;
    if (leerEntero(ui.n) !== n) ui.n.value = String(n);
    while (estado.acompanantes.length < n) crearAcompanante(estado.acompanantes.length + 1);
    estado.acompanantes.forEach((slot, i) => {
      plegar(slot.envoltorio, i < n);
      if (i >= n) quitarError(`acompanantes.${i}.nombre`);
    });
    estado.personas.forEach((p, clave) => {
      const visible = clave === 'titular' || p.numero <= n;
      plegar(p.envoltorio, visible);
      if (!visible) { quitarError(`alergias.${clave}`); quitarError(`alergias.${clave}.otras`); }
    });
    // Autocar: como mucho una plaza por persona (tú + acompañantes)
    const tope = Math.min(MAX_PLAZAS, 1 + n);
    [ui.ida, ui.vuelta].forEach((input) => {
      input.max = String(tope);
      const v = leerEntero(input);
      if (v !== null && v > tope) input.value = String(tope);
    });
    refrescarContadores();
    if (anunciarCambio) anunciar(n === 0 ? 'Sin acompañantes' : n === 1 ? '1 acompañante' : `${n} acompañantes`);
  }

  /* ---------- Contadores −/+ ---------- */
  function leerEntero(input) {
    const v = parseInt(input.value, 10);
    return Number.isFinite(v) ? v : null;
  }
  function limites(input) {
    return [Number(input.min) || 0, Number(input.max) || 0];
  }
  function refrescarContadores() {
    $$('[data-rsvp-contador]').forEach((caja) => {
      const input = caja.querySelector('input');
      const [min, max] = limites(input);
      const v = leerEntero(input);
      const valor = v === null ? min : v;
      caja.querySelectorAll('[data-paso]').forEach((b) => {
        const tope = Number(b.getAttribute('data-paso')) < 0 ? valor <= min : valor >= max;
        b.setAttribute('aria-disabled', tope ? 'true' : 'false');
      });
    });
  }
  function alCambiarContador(input, valor, anunciarlo) {
    if (input === ui.n) {
      quitarError('acompanantes');
      fijarAcompanantes(valor, { anunciarCambio: anunciarlo });
    } else {
      quitarError(input === ui.ida ? 'transporte.ida' : 'transporte.vuelta');
      quitarError('transporte');
      refrescarContadores();
      if (anunciarlo) anunciar(`${input === ui.ida ? 'Ida' : 'Vuelta'}: ${valor} ${valor === 1 ? 'plaza' : 'plazas'}`);
    }
    guardarPronto();
  }
  $$('[data-rsvp-contador]').forEach((caja) => {
    const input = caja.querySelector('input');
    caja.querySelectorAll('[data-paso]').forEach((boton) => {
      boton.addEventListener('click', () => {
        if (boton.getAttribute('aria-disabled') === 'true') return;
        const [min, max] = limites(input);
        const actual = leerEntero(input);
        const v = limitar((actual === null ? min : actual) + Number(boton.getAttribute('data-paso')), min, max);
        input.value = String(v);
        alCambiarContador(input, v, true);
      });
    });
    input.addEventListener('input', () => {
      const v = leerEntero(input);
      if (v === null) return; // a medio escribir
      const [min, max] = limites(input);
      const ok = limitar(v, min, max);
      if (input.value !== String(ok)) input.value = String(ok);
      alCambiarContador(input, ok, false);
    });
    input.addEventListener('change', () => {
      const [min, max] = limites(input);
      const actual = leerEntero(input);
      const v = limitar(actual === null ? min : actual, min, max);
      input.value = String(v);
      alCambiarContador(input, v, false);
    });
    input.addEventListener('focus', () => { try { input.select(); } catch (e) { /* sin selección */ } });
  });

  /* ---------- ¿Podrás asistir? ---------- */
  function valorAsistencia() {
    const r = ui.radios.find((x) => x.checked);
    return r ? r.value : '';
  }
  function pintarAsistencia() {
    plegar(ui.detalles, valorAsistencia() === 'si');
    ui.radios.forEach((r) => {
      const caja = r.closest('.rsvp-opcion');
      if (caja) caja.classList.toggle('rsvp-opcion--activa', r.checked);
    });
  }
  ui.radios.forEach((r) => r.addEventListener('change', () => {
    pintarAsistencia();
    quitarError('asistencia');
    guardarPronto();
  }));

  /* ---------- Errores ---------- */
  function destino(clave) {
    let m;
    if (clave === 'nombre') return { foco: ui.nombre, error: $('#rsvp-nombre-error'), controles: [ui.nombre] };
    if (clave === 'asistencia') {
      return { foco: ui.radios.find((r) => r.checked) || ui.radios[0], error: $('#rsvp-asistencia-error'), controles: ui.radios };
    }
    if (clave === 'acompanantes') return { foco: ui.n, error: $('#rsvp-n-error'), controles: [ui.n] };
    if ((m = /^acompanantes\.(\d+)\.nombre$/.exec(clave))) {
      const slot = estado.acompanantes[Number(m[1])];
      return slot ? { foco: slot.input, error: slot.error, controles: [slot.input] } : null;
    }
    if (clave === 'transporte' || clave === 'transporte.ida') return { foco: ui.ida, error: $('#rsvp-ida-error'), controles: [ui.ida] };
    if (clave === 'transporte.vuelta') return { foco: ui.vuelta, error: $('#rsvp-vuelta-error'), controles: [ui.vuelta] };
    if (clave === 'alergias' || (m = /^alergias\.([a-z0-9_]+?)(\.otras)?$/.exec(clave))) {
      const p = estado.personas.get(m ? m[1] : 'titular');
      if (!p) return null;
      return m && m[2]
        ? { foco: p.otras, error: p.error, controles: [p.otras] }
        : { foco: p.casillas[0], error: p.error, controles: [] };
    }
    if (clave === 'mensaje') return { foco: ui.mensaje, error: $('#rsvp-mensaje-error'), controles: [ui.mensaje] };
    return null; // se muestra como aviso general
  }
  function ponerError(clave, mensaje) {
    const d = destino(clave);
    if (!d || !d.error) return null;
    d.error.textContent = mensaje;
    d.error.hidden = false;
    d.controles.forEach((c) => c.setAttribute('aria-invalid', 'true'));
    estado.errores.set(clave, d);
    return d;
  }
  function quitarError(clave) {
    const d = estado.errores.get(clave);
    if (!d) return;
    estado.errores.delete(clave);
    const compartido = Array.from(estado.errores.values()).some((o) => o.error === d.error);
    if (!compartido) { d.error.textContent = ''; d.error.hidden = true; }
    d.controles.forEach((c) => c.removeAttribute('aria-invalid'));
  }
  function quitarErrores() {
    Array.from(estado.errores.keys()).forEach(quitarError);
  }
  function mostrarErrores(errores) {
    quitarErrores();
    const generales = [];
    let primero = null;
    Object.keys(errores).forEach((clave) => {
      const mensaje = String(errores[clave]);
      const d = ponerError(clave, mensaje);
      if (!d) { generales.push(mensaje); return; }
      if (d.foco && (!primero || (d.foco.compareDocumentPosition(primero) & Node.DOCUMENT_POSITION_FOLLOWING))) primero = d.foco;
    });
    if (generales.length) mostrarAviso({ tipo: 'error', titulo: generales.join(' ') });
    if (primero) enfocar(primero, 'center');
    else if (generales.length) desplazarA(ui.aviso, 'center');
  }

  function errorNombre(valor, vacio) {
    const v = limpiar(valor);
    if (!v) return vacio;
    if (v.length > 120) return TXT.nombreLargo;
    if (v.length < 2 || !RE_LETRA.test(v)) return TXT.nombreNoValido;
    return '';
  }
  function revalidarNombre(input, clave, vacio) {
    if (!estado.errores.has(clave)) return;
    const msg = errorNombre(input.value, vacio);
    if (msg) ponerError(clave, msg); else quitarError(clave);
  }
  ui.nombre.addEventListener('input', () => revalidarNombre(ui.nombre, 'nombre', TXT.nombreVacio));

  function validar() {
    const e = {};
    const n1 = errorNombre(ui.nombre.value, TXT.nombreVacio);
    if (n1) e.nombre = n1;
    const asistencia = valorAsistencia();
    if (!asistencia) e.asistencia = TXT.asistencia;
    if (asistencia === 'si') {
      for (let i = 0; i < estado.n; i++) {
        const msg = errorNombre(estado.acompanantes[i].input.value, TXT.acompananteVacio);
        if (msg) e[`acompanantes.${i}.nombre`] = msg;
      }
    }
    return e;
  }

  function alTocarPersona(ev) {
    const caja = ev.target.closest('[data-persona]');
    if (!caja) return;
    const clave = caja.getAttribute('data-persona');
    quitarError(`alergias.${clave}`);
    quitarError(`alergias.${clave}.otras`);
    if (clave === 'titular') quitarError('alergias');
  }
  ui.listaPersonas.addEventListener('input', alTocarPersona);
  ui.listaPersonas.addEventListener('change', alTocarPersona);

  /* ---------- Mensaje ---------- */
  function actualizarCuenta() {
    const n = ui.mensaje.value.length;
    const max = ui.mensaje.maxLength > 0 ? ui.mensaje.maxLength : 1000;
    if (ui.cuenta) {
      ui.cuenta.hidden = n < max * 0.8;
      ui.cuenta.textContent = `${n} / ${max}`;
    }
    if (n >= max && !estado.avisoLimite) anunciar(`Has llegado al máximo de ${max} caracteres.`);
    estado.avisoLimite = n >= max;
  }
  ui.mensaje.addEventListener('input', () => { actualizarCuenta(); quitarError('mensaje'); });

  /* ---------- Datos a enviar ---------- */
  function recogerDatos() {
    const asistencia = valorAsistencia();
    const si = asistencia === 'si';
    const n = si ? estado.n : 0;
    const tope = 1 + n;
    const datos = {
      nombre: limpiar(ui.nombre.value),
      asistencia,
      acompanantes: estado.acompanantes.slice(0, n).map((s) => ({ nombre: limpiar(s.input.value) })),
      transporte: {
        ida: si ? limitar(leerEntero(ui.ida) || 0, 0, tope) : 0,
        vuelta: si ? limitar(leerEntero(ui.vuelta) || 0, 0, tope) : 0,
      },
      alergias: [],
      mensaje: String(ui.mensaje.value || '').trim(),
    };
    if (si) {
      ['titular'].concat(datos.acompanantes.map((_, i) => `acompanante_${i + 1}`)).forEach((clave) => {
        const p = estado.personas.get(clave);
        if (!p) return;
        const opciones = p.casillas.filter((c) => c.checked).map((c) => c.value);
        const otras = limpiar(p.otras.value);
        if (opciones.length || otras) datos.alergias.push({ persona: clave, opciones, otras });
      });
    }
    return datos;
  }

  /* ---------- Avisos (error / sin conexión) ---------- */
  function limpiarAviso() {
    ui.aviso.textContent = '';
    estado.avisoSinConexion = false;
  }
  function mostrarAviso({ tipo = 'error', titulo, texto = '', acciones = [] }) {
    const caja = document.createElement('div');
    caja.className = `rsvp-aviso rsvp-aviso--${tipo}`;
    const t = document.createElement('p');
    t.className = 'rsvp-aviso__titulo';
    t.textContent = titulo;
    caja.appendChild(t);
    if (texto) {
      const p = document.createElement('p');
      p.textContent = texto;
      caja.appendChild(p);
    }
    if (acciones.length) {
      const fila = document.createElement('p');
      fila.className = 'rsvp-aviso__acciones';
      acciones.forEach((a) => fila.appendChild(a));
      caja.appendChild(fila);
    }
    ui.aviso.textContent = '';
    ui.aviso.appendChild(caja);
  }

  /** WhatsApp o correo de los novios, si están configurados (en esta sección o en #alojamiento). */
  function contacto() {
    const alojamiento = document.getElementById('alojamiento');
    const leer = (attr) => (raiz.getAttribute(attr) || (alojamiento && alojamiento.getAttribute(attr)) || '').trim();
    const tel = leer('data-whatsapp').replace(/\D+/g, '');
    const email = leer('data-email');
    return { tel, email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? email : '' };
  }
  /** La respuesta en texto, para mandarla a mano si la web falla. */
  function textoManual(d) {
    const l = ['Hola, Marta y Jorge. No he podido enviar el formulario de la web, así que os mando mi respuesta por aquí:', ''];
    l.push(`Nombre: ${d.nombre}`);
    l.push(`¿Asistiré? ${d.asistencia === 'si' ? 'Sí' : 'No'}`);
    if (d.asistencia === 'si') {
      if (d.acompanantes.length) l.push(`Acompañantes: ${d.acompanantes.map((a) => a.nombre).join(', ')}`);
      if (d.transporte.ida || d.transporte.vuelta) l.push(`Autocar: ${d.transporte.ida} de ida y ${d.transporte.vuelta} de vuelta`);
      d.alergias.forEach((a) => {
        const quien = a.persona === 'titular' ? d.nombre : (d.acompanantes[Number(a.persona.split('_')[1]) - 1] || {}).nombre;
        const cosas = a.opciones.map((o) => ETIQUETAS_ALERGIA[o] || o).concat(a.otras ? [a.otras] : []);
        l.push(`Alergias de ${quien}: ${cosas.join(', ')}`);
      });
    }
    if (d.mensaje) l.push('', d.mensaje);
    return l.join('\n').slice(0, 1500);
  }
  function enlacesContacto(datos) {
    const { tel, email } = contacto();
    const enlaces = [];
    if (tel) {
      const a = document.createElement('a');
      a.className = 'boton';
      a.href = `https://wa.me/${tel}?text=${encodeURIComponent(textoManual(datos))}`;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = TXT.whatsapp;
      enlaces.push(a);
    }
    if (email) {
      const a = document.createElement('a');
      a.className = 'boton';
      a.href = `mailto:${email}?subject=${encodeURIComponent('Confirmación de asistencia')}&body=${encodeURIComponent(textoManual(datos))}`;
      a.textContent = TXT.correo;
      enlaces.push(a);
    }
    return enlaces;
  }
  function avisoError(datos) {
    mostrarAviso({ tipo: 'error', titulo: TXT.errorTitulo, texto: TXT.errorTexto, acciones: enlacesContacto(datos) });
    desplazarA(ui.aviso, 'nearest');
  }
  function avisoSinConexion() {
    mostrarAviso({ tipo: 'error', titulo: TXT.sinConexionTitulo, texto: TXT.sinConexionTexto });
    estado.avisoSinConexion = true;
    desplazarA(ui.aviso, 'nearest');
  }
  window.addEventListener('online', () => {
    if (!estado.avisoSinConexion) return;
    mostrarAviso({ tipo: 'info', titulo: TXT.conexionVuelve });
    estado.avisoSinConexion = false;
  });

  /* ---------- Envío ---------- */
  function ponerEnviando(si) {
    estado.enviando = si;
    ui.enviar.setAttribute('aria-disabled', si ? 'true' : 'false');
    ui.enviar.classList.toggle('rsvp-enviar--enviando', si);
    if (ui.enviarTexto) ui.enviarTexto.textContent = si ? TXT.enviando : TXT.enviar;
    form.setAttribute('aria-busy', si ? 'true' : 'false');
    if (si) anunciar('Enviando tu respuesta…');
  }

  async function enviarConReintento(datos) {
    for (let intento = 1; intento <= 2; intento++) {
      const cuerpo = {
        submission_id: estado.submissionId,
        ...datos,
        web: ui.trampa ? ui.trampa.value : '',
        t: Math.round(performance.now() - inicio),
      };
      const ctrl = typeof AbortController === 'function' ? new AbortController() : null;
      const reloj = ctrl ? setTimeout(() => ctrl.abort(), LIMITE_PETICION) : 0;
      try {
        const r = await fetch(ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify(cuerpo),
          credentials: 'same-origin',
          cache: 'no-store',
          signal: ctrl ? ctrl.signal : undefined,
        });
        let json = null;
        try { json = await r.json(); } catch (e) { /* respuesta sin JSON */ }
        return { tipo: 'respuesta', status: r.status, json };
      } catch (err) {
        // Fallo de red o tiempo agotado: UN reintento con el MISMO submission_id (no duplica).
        if (intento === 1 && navigator.onLine !== false) { await pausa(1200); continue; }
        return { tipo: 'red', sinConexion: navigator.onLine === false };
      } finally {
        clearTimeout(reloj);
      }
    }
    return { tipo: 'red', sinConexion: navigator.onLine === false };
  }

  async function enviarFormulario() {
    if (estado.enviando) return;
    limpiarAviso();
    const errores = validar();
    if (Object.keys(errores).length) { mostrarErrores(errores); return; }
    quitarErrores();
    if (navigator.onLine === false) { avisoSinConexion(); return; }

    const datos = recogerDatos();
    const firma = JSON.stringify(datos);
    if (!estado.intento || estado.intento.firma !== firma) {
      // Si cambian los datos tras un intento fallido, es un envío nuevo.
      if (estado.intento) estado.submissionId = nuevoId();
      estado.intento = { id: estado.submissionId, firma };
      guardarBorrador();
    }

    ponerEnviando(true);
    let resultado;
    try {
      const espera = ESPERA_MINIMA - (performance.now() - inicio);
      if (espera > 0) await pausa(espera);
      resultado = await enviarConReintento(datos);
    } catch (e) {
      resultado = { tipo: 'red', sinConexion: navigator.onLine === false };
    } finally {
      ponerEnviando(false);
    }

    if (resultado.tipo === 'respuesta') {
      const ok = !!(resultado.json && resultado.json.ok === true);
      if ((resultado.status === 200 || resultado.status === 201) && ok) { exito(datos); return; }
      if (resultado.status === 400 && resultado.json && resultado.json.errores && typeof resultado.json.errores === 'object') {
        mostrarErrores(resultado.json.errores);
        return;
      }
      avisoError(datos);
      return;
    }
    if (resultado.sinConexion) avisoSinConexion(); else avisoError(datos);
  }
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    enviarFormulario();
  });

  /* ---------- Agradecimiento ---------- */
  const SEGUNDOS_NOMBRES = ['jose', 'maria', 'luis', 'carlos', 'antonio', 'manuel', 'jesus', 'javier', 'ignacio',
    'miguel', 'angel', 'pablo', 'belen', 'isabel', 'carmen', 'luisa', 'teresa', 'pilar', 'elena', 'eugenia',
    'victoria', 'ramon', 'andres', 'alberto', 'enrique', 'francisco', 'fernando', 'cristina', 'rosa', 'mar'];
  const sinTildes = (s) => (typeof s.normalize === 'function' ? s.normalize('NFD').replace(/[\u0300-\u036F]/g, '') : s).toLowerCase();
  /** «ana garcía lópez» → «Ana»; «José Luis Pérez» → «José Luis». */
  function nombreDePila(nombre) {
    const partes = limpiar(nombre).split(' ').filter(Boolean);
    if (!partes.length) return '';
    const pila = partes.length >= 3 && SEGUNDOS_NOMBRES.includes(sinTildes(partes[1])) ? partes.slice(0, 2) : partes.slice(0, 1);
    return pila.map((p) => p.charAt(0).toLocaleUpperCase('es') + p.slice(1)).join(' ');
  }
  /** Resumen en líneas cortas: «3 personas» / «Autocar: 3 ida · 2 vuelta». */
  function lineasResumen(d) {
    const personas = 1 + d.acompanantes.length;
    const lineas = [personas === 1 ? '1 persona' : `${personas} personas`];
    const { ida, vuelta } = d.transporte;
    if (ida || vuelta) lineas.push(`Autocar: ${ida} de ida · ${vuelta} de vuelta`);
    return lineas;
  }
  function exito(datos) {
    borrarBorrador();
    estado.submissionId = nuevoId();
    estado.intento = null;
    limpiarAviso();
    const si = datos.asistencia === 'si';
    const nombre = nombreDePila(datos.nombre);
    ui.graciasTitulo.textContent = nombre ? `¡Gracias, ${nombre}!` : '¡Gracias!';
    if (ui.graciasTexto) ui.graciasTexto.textContent = ui.gracias.getAttribute(si ? 'data-texto-si' : 'data-texto-no') || '';
    if (ui.graciasResumen) {
      ui.graciasResumen.textContent = '';
      (si ? lineasResumen(datos) : []).forEach((linea) => {
        const span = document.createElement('span');
        span.textContent = linea;
        ui.graciasResumen.appendChild(span);
      });
      ui.graciasResumen.hidden = !si;
    }
    form.hidden = true;
    ui.gracias.hidden = false;
    try { ui.graciasTitulo.focus({ preventScroll: true }); } catch (e) { ui.graciasTitulo.focus(); }
    desplazarA(ui.gracias, 'center');
  }
  if (ui.modificar) {
    ui.modificar.addEventListener('click', () => {
      ui.gracias.hidden = true;
      form.hidden = false;
      guardarBorrador();
      try { form.focus({ preventScroll: true }); } catch (e) { form.focus(); }
      desplazarA(raiz.querySelector('.rsvp__tarjeta') || form, 'start');
      anunciar('Puedes cambiar tu respuesta y volver a enviarla.');
    });
  }

  /* ---------- Borrador (por si se recarga la página) ---------- */
  function datosBorrador() {
    return {
      v: 1,
      t: Date.now(),
      nombre: ui.nombre.value,
      asistencia: valorAsistencia(),
      n: estado.n,
      acompanantes: estado.acompanantes.map((s) => s.input.value),
      ida: leerEntero(ui.ida) || 0,
      vuelta: leerEntero(ui.vuelta) || 0,
      alergias: Array.from(estado.personas, ([clave, p]) => [clave, p.casillas.filter((c) => c.checked).map((c) => c.value), p.otras.value]),
      mensaje: ui.mensaje.value,
      intento: estado.intento,
    };
  }
  function guardarBorrador() {
    if (form.hidden) return; // ya enviado
    try { window.localStorage.setItem(CLAVE_BORRADOR, JSON.stringify(datosBorrador())); } catch (e) { /* modo privado o sin espacio */ }
  }
  let relojBorrador;
  function guardarPronto() {
    clearTimeout(relojBorrador);
    relojBorrador = setTimeout(guardarBorrador, 400);
  }
  function borrarBorrador() {
    clearTimeout(relojBorrador);
    try { window.localStorage.removeItem(CLAVE_BORRADOR); } catch (e) { /* sin almacenamiento */ }
  }
  function leerBorrador() {
    try {
      const b = JSON.parse(window.localStorage.getItem(CLAVE_BORRADOR) || 'null');
      if (!b || typeof b !== 'object' || b.v !== 1) return null;
      if (!(Date.now() - Number(b.t) < CADUCIDAD_BORRADOR)) { borrarBorrador(); return null; }
      return b;
    } catch (e) {
      return null;
    }
  }
  function tieneContenido(b) {
    return !!(String(b.nombre || '').trim() || b.asistencia || String(b.mensaje || '').trim() ||
      (Array.isArray(b.acompanantes) && b.acompanantes.some((x) => String(x || '').trim())));
  }
  function restaurar(b) {
    const texto = (v, max) => String(v == null ? '' : v).slice(0, max);
    ui.nombre.value = texto(b.nombre, 120);
    ui.radios.forEach((r) => { r.checked = r.value === b.asistencia; });
    const nombres = Array.isArray(b.acompanantes) ? b.acompanantes.slice(0, MAX_ACOMPANANTES) : [];
    while (estado.acompanantes.length < nombres.length) crearAcompanante(estado.acompanantes.length + 1);
    nombres.forEach((v, i) => {
      estado.acompanantes[i].input.value = texto(v, 120);
      ponerTituloPersona(i + 1);
    });
    fijarAcompanantes(Number(b.n) || 0);
    ui.ida.value = String(limitar(Number(b.ida) || 0, 0, Number(ui.ida.max) || 1));
    ui.vuelta.value = String(limitar(Number(b.vuelta) || 0, 0, Number(ui.vuelta.max) || 1));
    (Array.isArray(b.alergias) ? b.alergias : []).forEach((fila) => {
      if (!Array.isArray(fila)) return;
      const p = estado.personas.get(fila[0]);
      if (!p) return;
      const marcadas = Array.isArray(fila[1]) ? fila[1] : [];
      p.casillas.forEach((c) => { c.checked = marcadas.includes(c.value); });
      p.otras.value = texto(fila[2], 300);
    });
    ui.mensaje.value = texto(b.mensaje, 1000);
    const i = b.intento;
    if (i && typeof i === 'object' && RE_UUID.test(String(i.id)) && typeof i.firma === 'string') {
      estado.intento = { id: String(i.id), firma: i.firma };
      estado.submissionId = estado.intento.id;
    }
  }
  if (ui.vaciar) {
    ui.vaciar.addEventListener('click', () => {
      form.reset();
      borrarBorrador();
      estado.intento = null;
      estado.submissionId = nuevoId();
      quitarErrores();
      limpiarAviso();
      estado.acompanantes.forEach((s) => ponerTituloPersona(s.numero));
      fijarAcompanantes(0);
      pintarAsistencia();
      actualizarCuenta();
      if (ui.recuperado) ui.recuperado.hidden = true;
      ui.nombre.focus();
    });
  }
  form.addEventListener('input', guardarPronto);
  form.addEventListener('change', guardarPronto);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') guardarBorrador(); });
  window.addEventListener('pagehide', guardarBorrador);

  /* ---------- Intro en un campo de texto: pasa al siguiente en vez de enviar ---------- */
  form.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter' || ev.isComposing || ev.defaultPrevented) return;
    const t = ev.target;
    if (!(t instanceof HTMLInputElement) || ['checkbox', 'radio', 'submit', 'button', 'reset'].includes(t.type)) return;
    ev.preventDefault();
    const lista = $$('input, textarea, select, button').filter((x) => !x.disabled && x.tabIndex !== -1 &&
      x.type !== 'hidden' && !x.closest('[inert]') && !x.closest('[hidden]') && x.getClientRects().length > 0);
    const siguiente = lista[lista.indexOf(t) + 1];
    if (siguiente) siguiente.focus();
  });

  /* ---------- Arranque ---------- */
  form.classList.add('rsvp-sin-animacion');
  form.setAttribute('tabindex', '-1');
  crearPersona('titular', 0);
  plegar(ui.detalles, false);
  const borrador = leerBorrador();
  if (borrador) restaurar(borrador); else fijarAcompanantes(0);
  pintarAsistencia();
  refrescarContadores();
  actualizarCuenta();
  if (borrador && tieneContenido(borrador) && ui.recuperado) ui.recuperado.hidden = false;
  ui.enviar.disabled = false;
  form.classList.add('rsvp-listo');
  requestAnimationFrame(() => requestAnimationFrame(() => form.classList.remove('rsvp-sin-animacion')));
})();
