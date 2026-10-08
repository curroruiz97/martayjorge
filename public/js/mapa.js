/*!
 * Marta & Jorge · mapa de alojamiento (Leaflet 1.9.4 autoalojado)
 *
 * Integración (ya hecha en index.html):
 *   <link rel="stylesheet" href="css/mapa.css">
 *   <div id="mapa-alojamiento" class="mapa marco" role="region" aria-label="…"></div>
 *   <script src="js/mapa.js" defer></script>
 * El tamaño del contenedor lo da el CSS (aspect-ratio), así que no hay saltos de layout.
 *
 * Carga perezosa: Leaflet (JS + CSS, vendor/leaflet/) solo se descarga cuando el mapa está a
 * ~300 px de entrar en pantalla. Si no hay JS o falla la descarga, queda el círculo dibujado
 * (CSS) y el enlace «Abrir en Google Maps» que hay debajo.
 *
 * Qué dibuja: la zona recomendada para alojarse (círculo «a rotulador»: contorno irregular
 * ±2–4 % con semilla fija, trazo discontinuo terracota, relleno suave y rótulo manuscrito) y dos
 * marcadores (Iglesia de San Pablo y parking de la Plaza de Portugalete) con «¿Cómo llegar?».
 * Sin secuestrar el scroll: la rueda solo hace zoom tras hacer clic; en táctil se mueve el mapa
 * con DOS dedos (con uno se desplaza la página y sale un aviso).
 *
 * Todos los datos geográficos están en CFG (más abajo); su origen y fiabilidad, en
 * docs/datos-verificados.md. Evento al terminar: «mapa:listo» sobre el contenedor (detail.map).
 */
(function () {
  'use strict';

  var el = document.getElementById('mapa-alojamiento');
  if (!el || el.getAttribute('data-mapa')) return;
  el.setAttribute('data-mapa', 'pendiente');

  /* ---------------------------------------------------------------------------------------
     Configuración
     --------------------------------------------------------------------------------------- */
  var CFG = {
    // Baricentro de Plaza Mayor · Catedral/Plaza de Portugalete · Iglesia de San Pablo.
    centro: [41.65423, -4.72563],
    radio: 900,                 // metros (≈ 11 min andando); cubre también la Plaza del Poniente
    semilla: 20270508,          // fija: el trazo «a mano» sale siempre igual (fecha de la boda)
    color: '#a4563a',           // --terracota
    zoomMin: 14, zoomMax: 18, zoomMaxEncuadre: 15,
    teselas: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    atribucion:
      '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors ' +
      '© <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a>',
    rotulo: ['Zona recomendada', 'para alojarse'],
    rotuloPos: [-0.06, -0.50],  // desplazamiento del rótulo desde el centro, en fracciones del radio [este, norte]
    puntos: [
      {
        tipo: 'iglesia', nombre: 'Iglesia de San Pablo', etiqueta: 'San Pablo',
        detalle: 'Ceremonia · 12:00',
        pos: [41.65710, -4.72442],
        destino: 'Iglesia de San Pablo, Plaza de San Pablo, 47011 Valladolid'
      },
      {
        tipo: 'parking', nombre: 'Parking Plaza de Portugalete', etiqueta: 'Parking',
        detalle: 'Junto a la Catedral, a unos 500 m',
        pos: [41.65335, -4.72386],
        destino: 'Parking Plaza de Portugalete, Valladolid'
      }
    ]
  };

  var TXT = {
    dosDedos: 'Usa dos dedos para mover el mapa',
    rueda: 'Haz clic en el mapa para usar la rueda',
    comoLlegar: '¿Cómo llegar?',
    abrirMaps: 'Abrir en Google Maps',
    acercar: 'Acercar el mapa',
    alejar: 'Alejar el mapa',
    cerrar: 'Cerrar',
    error: 'No hemos podido cargar el mapa:',
    errorEnlace: 'ábrelo en Google Maps'
  };

  var URL_ZONA = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent('Plaza Mayor, Valladolid');

  function urlRuta(destino) {
    return 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(destino);
  }

  /* ---------------------------------------------------------------------------------------
     Geometría: círculo «a rotulador»
     --------------------------------------------------------------------------------------- */
  var TAU = Math.PI * 2;

  // PRNG con semilla (mulberry32): mismo resultado siempre.
  function prng(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Punto a «metros» del centro en el ángulo ang (0 = este, π/2 = norte).
  function desplazar(c, metros, ang) {
    return [
      c[0] + (metros * Math.sin(ang)) / 111320,
      c[1] + (metros * Math.cos(ang)) / (111320 * Math.cos(c[0] * Math.PI / 180))
    ];
  }

  // Devuelve { relleno: anillo cerrado, trazo: una vuelta y un poco más (el rotulador «se pasa») }.
  function circuloARotulador(c, R, semilla) {
    var rnd = prng(semilla);
    // Irregularidad suave: armónicos de baja frecuencia (≈ ±2,5 % del radio) + un temblor muy fino.
    var h = [[2, 0.009], [3, 0.008], [5, 0.005], [9, 0.002], [14, 0.0012]].map(function (p) {
      return { k: p[0], a: p[1] * (0.75 + 0.5 * rnd()), f: rnd() * TAU };
    });
    function radio(ang) {
      var s = 0;
      for (var i = 0; i < h.length; i++) s += h[i].a * Math.sin(h[i].k * ang + h[i].f);
      return R * (1 + s);
    }
    var inicio = rnd() * TAU;
    var N = 150;
    var solape = 0.33;                 // radianes de más (≈ 19°)
    var deriva = 0.016;                // el final del trazo se abre ~1,6 % hacia fuera
    var relleno = [], trazo = [], i, ang;
    for (i = 0; i < N; i++) {
      ang = inicio + (i / N) * TAU;
      relleno.push(desplazar(c, radio(ang), ang));
    }
    var M = N + Math.round(N * solape / TAU);
    for (i = 0; i <= M; i++) {
      ang = inicio + (i / N) * TAU;
      var u = i / N;                                    // 0 … 1,05
      var s = Math.min(1, Math.max(0, (u - 0.72) / (1 + solape / TAU - 0.72)));
      s = s * s * (3 - 2 * s);
      trazo.push(desplazar(c, radio(ang) * (1 + deriva * s), ang));
    }
    return { relleno: relleno, trazo: trazo };
  }

  /* ---------------------------------------------------------------------------------------
     Marcadores a pluma (SVG en línea)
     --------------------------------------------------------------------------------------- */
  var GOTA = 'M22.4 49.4C21.3 48.1 6.7 33.6 6.5 20.7 6.3 11.4 13.1 3.7 22.1 3.5 31.2 3.3 38 10.6 37.7 20.2 37.3 33 23.6 48 22.4 49.4Z';
  var PIN = {
    iglesia: { fill: '#a4563a', glifo: 'M22 10.8v18.2M15.2 17.6h13.6' },
    parking: { fill: '#6c7550', glifo: 'M17.6 28.6V12.2h6c3.9 0 5.7 2.4 5.7 5.2 0 2.9-1.9 5.3-5.8 5.3h-5.9' }
  };
  function svgPin(tipo) {
    var p = PIN[tipo];
    return '<svg class="mapa-pin__svg" viewBox="0 0 44 52" width="44" height="52" aria-hidden="true" focusable="false">' +
      '<ellipse cx="22" cy="50.4" rx="8" ry="1.7" fill="#2b2a28" opacity=".2"/>' +
      '<path d="' + GOTA + '" fill="' + p.fill + '" stroke="#2b2a28" stroke-width="2.2" stroke-linejoin="round"/>' +
      '<path d="' + p.glifo + '" fill="none" stroke="#fbf8f1" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>' +
      '</svg>';
  }

  /* ---------------------------------------------------------------------------------------
     Carga perezosa de Leaflet
     --------------------------------------------------------------------------------------- */
  var BASE = (function () {
    var attr = el.getAttribute('data-leaflet');
    if (attr) return attr.replace(/\/?$/, '/');
    try {
      var s = document.currentScript;
      return new URL('../vendor/leaflet/', s && s.src ? s.src : location.href).href;
    } catch (e) { return 'vendor/leaflet/'; }
  })();

  function cargarEstilos(href) {
    return new Promise(function (ok, ko) {
      var l = document.createElement('link');
      l.rel = 'stylesheet'; l.href = href;
      l.onload = function () { ok(); };
      l.onerror = function () { ko(new Error('css')); };
      document.head.appendChild(l);
    });
  }
  function cargarScript(src) {
    return new Promise(function (ok, ko) {
      var s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = function () { ok(); };
      s.onerror = function () { ko(new Error('js')); };
      document.head.appendChild(s);
    });
  }
  function cargarLeaflet() {
    if (window.L && window.L.map) return Promise.resolve();
    // Calienta la conexión con las teselas mientras baja Leaflet.
    ['a', 'b'].forEach(function (n) {
      var p = document.createElement('link');
      p.rel = 'preconnect'; p.href = 'https://' + n + '.basemaps.cartocdn.com';
      document.head.appendChild(p);
    });
    return Promise.all([cargarEstilos(BASE + 'leaflet.css'), cargarScript(BASE + 'leaflet.js')]).then(function () {
      if (!(window.L && window.L.map)) throw new Error('L');
    });
  }

  function cuandoEstéCerca(fn) {
    if (!('IntersectionObserver' in window)) {
      if (document.readyState === 'complete') fn(); else window.addEventListener('load', fn, { once: true });
      return;
    }
    var io = new IntersectionObserver(function (entradas) {
      for (var i = 0; i < entradas.length; i++) {
        if (entradas[i].isIntersecting) { io.disconnect(); fn(); return; }
      }
    }, { rootMargin: '300px 0px' });
    io.observe(el);
  }

  function mostrarError() {
    el.setAttribute('data-mapa', 'error');
    if (el.querySelector('.mapa__error')) return;
    var d = document.createElement('div');
    d.className = 'mapa__error';
    var p = document.createElement('p');
    p.appendChild(document.createTextNode(TXT.error + ' '));
    var a = document.createElement('a');
    a.href = URL_ZONA; a.target = '_blank'; a.rel = 'noopener';
    a.textContent = TXT.errorEnlace;
    p.appendChild(a);
    p.appendChild(document.createTextNode('.'));
    d.appendChild(p);
    el.appendChild(d);
  }

  /* ---------------------------------------------------------------------------------------
     El mapa
     --------------------------------------------------------------------------------------- */
  function crearMapa() {
    var L = window.L;
    var reducir = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
    // Pantalla táctil «de verdad» (móvil/tablet): un dedo desplaza la página, dos mueven el mapa.
    var tactil = !!(window.matchMedia && matchMedia('(hover: none) and (pointer: coarse)').matches);

    var lienzo = document.createElement('div');
    lienzo.className = 'mapa__lienzo';
    lienzo.setAttribute('lang', 'es');
    el.appendChild(lienzo);

    var map = L.map(lienzo, {
      center: CFG.centro, zoom: CFG.zoomMaxEncuadre,
      minZoom: CFG.zoomMin, maxZoom: CFG.zoomMax,
      zoomControl: false, attributionControl: false,
      scrollWheelZoom: false,           // se activa al hacer clic (ver más abajo)
      dragging: !tactil,                // táctil: el pellizco con dos dedos también desplaza (touchZoom)
      touchZoom: true,
      zoomSnap: 1, zoomDelta: 1, bounceAtZoomLimits: false,
      keyboard: true,
      zoomAnimation: !reducir, fadeAnimation: !reducir, markerZoomAnimation: !reducir, inertia: !reducir
    });

    /* Teselas + atribución visible */
    var capa = L.tileLayer(CFG.teselas, {
      subdomains: 'abcd', maxZoom: 20, minZoom: 0, attribution: CFG.atribucion, crossOrigin: false
    }).addTo(map);
    L.control.attribution({ prefix: '<a href="https://leafletjs.com" target="_blank" rel="noopener">Leaflet</a>' }).addTo(map);
    L.control.zoom({ position: 'topleft', zoomInTitle: TXT.acercar, zoomOutTitle: TXT.alejar }).addTo(map);

    /* Círculo a rotulador */
    var geo = circuloARotulador(CFG.centro, CFG.radio, CFG.semilla);
    L.polygon(geo.relleno, {
      stroke: false, fillColor: CFG.color, fillOpacity: 0.1, interactive: false, smoothFactor: 0.4
    }).addTo(map);
    L.polyline(geo.trazo, {
      color: CFG.color, weight: 3, opacity: 0.95, dashArray: '10 9', lineCap: 'round', lineJoin: 'round',
      interactive: false, smoothFactor: 0.4, className: 'mapa-trazo'
    }).addTo(map);

    /* Rótulo manuscrito */
    var posRotulo = desplazar(CFG.centro, CFG.radio * Math.hypot(CFG.rotuloPos[0], CFG.rotuloPos[1]),
      Math.atan2(CFG.rotuloPos[1], CFG.rotuloPos[0]));
    L.marker(posRotulo, {
      interactive: false, keyboard: false, zIndexOffset: -500,
      icon: L.divIcon({
        className: 'mapa-rotulo', iconSize: [0, 0],
        html: '<span>' + CFG.rotulo.join('<br>') + '</span>'
      })
    }).addTo(map);

    /* Marcadores con ventana «¿Cómo llegar?» */
    var abiertoConTeclado = null;
    // Ancho útil de la ventana: que quepa a la derecha de los botones +/− (en móvil el mapa mide ~340 px)
    function anchoPopup() { return Math.max(150, Math.min(260, lienzo.clientWidth - 150)); }
    CFG.puntos.forEach(function (p) {
      var icono = L.divIcon({
        className: 'mapa-pin mapa-pin--' + p.tipo, iconSize: [44, 52], iconAnchor: [22, 50], popupAnchor: [0, -44],
        html: svgPin(p.tipo) + '<span class="mapa-pin__nombre" aria-hidden="true">' + p.etiqueta + '</span>'
      });
      var m = L.marker(p.pos, { icon: icono, title: p.nombre, alt: p.nombre, keyboard: true, riseOnHover: true }).addTo(map);
      m.getElement().setAttribute('aria-label', p.nombre);

      var c = document.createElement('div');
      c.className = 'mapa-popup';
      var t = document.createElement('strong'); t.className = 'mapa-popup__titulo'; t.textContent = p.nombre;
      var d = document.createElement('span'); d.className = 'mapa-popup__detalle'; d.textContent = p.detalle;
      var a = document.createElement('a'); a.className = 'boton'; a.href = urlRuta(p.destino);
      a.target = '_blank'; a.rel = 'noopener'; a.textContent = TXT.comoLlegar;
      var sr = document.createElement('span'); sr.className = 'sr-only';
      sr.textContent = ' a ' + p.nombre + ' (se abre en Google Maps)';
      a.appendChild(sr);
      c.appendChild(t); c.appendChild(d); c.appendChild(a);
      m.bindPopup(c, { minWidth: 150, maxWidth: anchoPopup(), autoPanPaddingTopLeft: [64, 16], autoPanPaddingBottomRight: [16, 16], closeButton: true });

      m.getElement().addEventListener('keydown', function (e) {
        if (e.key === 'Enter') abiertoConTeclado = m;
        else if (e.key === ' ') { e.preventDefault(); abiertoConTeclado = m; m.openPopup(); }   // role="button": Espacio también
      });
      m.on('popupopen', function (e) {
        var ancho = anchoPopup();                    // se adapta si ha girado el móvil o cambiado el tamaño
        if (e.popup.options.maxWidth !== ancho) { e.popup.options.maxWidth = ancho; e.popup.update(); }
        var cerrar = e.popup.getElement().querySelector('.leaflet-popup-close-button');
        if (cerrar) cerrar.setAttribute('aria-label', TXT.cerrar);
        if (abiertoConTeclado === m) {              // quien abre con teclado, sigue con teclado
          var enlace = e.popup.getElement().querySelector('a.boton');
          if (enlace) enlace.focus({ preventScroll: true });
        }
      });
      m.on('popupclose', function () {
        if (abiertoConTeclado === m) { abiertoConTeclado = null; m.getElement().focus({ preventScroll: true }); }
      });
    });

    // Escape cierra la ventana también cuando el foco está dentro de ella (Leaflet solo lo hace con el foco en el mapa)
    lienzo.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && lienzo.querySelector('.leaflet-popup')) { e.stopPropagation(); map.closePopup(); }
    });

    /* Encuadre: el mayor zoom entero en el que cabe el círculo entero */
    var limites = L.latLngBounds(geo.relleno);
    var tocado = false;
    function encuadrar() {
      map.invalidateSize({ animate: false });
      map.fitBounds(limites, { padding: [12, 12], maxZoom: CFG.zoomMaxEncuadre, animate: false });
    }
    encuadrar();
    map.setMaxBounds(limites.pad(1.5));
    map.options.maxBoundsViscosity = 0.9;

    ['pointerdown', 'touchstart', 'keydown', 'wheel'].forEach(function (ev) {
      lienzo.addEventListener(ev, function () { tocado = true; }, { passive: true });
    });
    var tRedim;
    window.addEventListener('resize', function () {
      clearTimeout(tRedim);
      tRedim = setTimeout(function () { map.invalidateSize({ animate: false }); if (!tocado) encuadrar(); }, 150);
    });

    /* Avisos discretos */
    var aviso = document.createElement('div');
    aviso.className = 'mapa__aviso';
    aviso.setAttribute('aria-hidden', 'true');
    el.appendChild(aviso);
    var tAviso;
    function avisar(texto) {
      aviso.textContent = texto;
      el.classList.add('mapa--aviso');
      clearTimeout(tAviso);
      tAviso = setTimeout(function () { el.classList.remove('mapa--aviso'); }, 1600);
    }

    /* Rueda: solo tras hacer clic en el mapa (ratón); se suelta al salir */
    function activarRueda() { map.scrollWheelZoom.enable(); el.classList.add('mapa--activo'); el.classList.remove('mapa--aviso'); }
    function soltarRueda() { map.scrollWheelZoom.disable(); el.classList.remove('mapa--activo'); }
    lienzo.addEventListener('pointerdown', function (e) { if (e.pointerType === 'mouse' || e.pointerType === 'pen') activarRueda(); });
    lienzo.addEventListener('mouseleave', soltarRueda);
    lienzo.addEventListener('wheel', function (e) {
      if (!tactil && !e.ctrlKey && !map.scrollWheelZoom.enabled()) avisar(TXT.rueda);
    }, { passive: true });

    /* Táctil: con un dedo se mueve la página (y avisamos); con dos, el mapa */
    if (tactil) {
      var ini = null;
      lienzo.addEventListener('touchstart', function (e) {
        ini = e.touches.length === 1 ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : null;
        if (e.touches.length > 1) el.classList.remove('mapa--aviso');
      }, { passive: true });
      lienzo.addEventListener('touchmove', function (e) {
        if (ini && e.touches.length === 1 &&
            Math.hypot(e.touches[0].clientX - ini.x, e.touches[0].clientY - ini.y) > 12) {
          ini = null; avisar(TXT.dosDedos);
        }
      }, { passive: true });
      lienzo.addEventListener('touchend', function () { ini = null; }, { passive: true });
    }

    el.classList.add('mapa--lista');
    el.setAttribute('data-mapa', 'listo');
    el.mapaLeaflet = map;
    // Una pasada más cuando ya están las fuentes (Caveat) y el layout asentado.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { if (!tocado) encuadrar(); });
    el.dispatchEvent(new CustomEvent('mapa:listo', { detail: { map: map, capaTeselas: capa } }));
  }

  /* ---------------------------------------------------------------------------------------
     Arranque
     --------------------------------------------------------------------------------------- */
  cuandoEstéCerca(function () {
    el.setAttribute('data-mapa', 'cargando');
    cargarLeaflet().then(crearMapa).catch(function () { mostrarError(); });
  });
})();
