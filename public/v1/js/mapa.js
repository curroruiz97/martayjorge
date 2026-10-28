/*!
 * Marta & Jorge · mapa de alojamiento (Google Maps JavaScript API, mapa vectorial con Map ID)
 *
 * Integración (ya hecha en index.html):
 *   <link rel="stylesheet" href="css/mapa.css">
 *   <div id="mapa-alojamiento" class="mapa marco" data-api-key="…" data-map-id="…" data-ilu-san-pablo="…" role="region" aria-label="…"></div>
 *   <aside class="mapa-leyenda">…</aside>          (leyenda en HTML: se ve también sin JS)
 *   <script src="js/mapa.js" defer></script>
 * El tamaño del contenedor lo da el CSS (aspect-ratio), así que no hay saltos de layout.
 *
 * Clave y estilo:
 *   · data-api-key: clave de Google Maps. Es pública por naturaleza (va al navegador); lo que la
 *     protege es la restricción por «sitios web» (HTTP referrer) en Google Cloud. Ver docs/mapa-google.md.
 *   · data-map-id: Map ID «martayjorge-web». Los colores del mapa (beige, río, parques, qué etiquetas se
 *     ven) se cambian en Google Cloud → Estilos de mapa, sin tocar este fichero.
 *
 * Carga perezosa: la API de Google solo se descarga cuando el mapa está a ~300 px de entrar en
 * pantalla. Sin JS, sin clave o si falla la descarga, queda el óvalo dibujado (CSS), la leyenda y el
 * enlace «Abrir en Google Maps» que hay debajo.
 *
 * Qué dibuja: la zona recomendada (óvalo grande), la zona más cómoda junto a la Plaza del Poniente
 * (óvalo discontinuo), los rótulos de las dos zonas y los puntos de referencia (San Pablo, Poniente,
 * Plaza Mayor, Catedral, Plaza de Zorrilla y Campo Grande). Los que tienen «¿Cómo llegar?» abren
 * una ventana al pulsarlos (ratón, dedo o teclado).
 * Sin secuestrar el scroll: gestureHandling «cooperative» (Ctrl + rueda en ordenador, dos dedos en móvil).
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
    apiKey: (el.getAttribute('data-api-key') || '').trim(),
    mapId: (el.getAttribute('data-map-id') || '').trim(),
    // El rojo sale de --rojo (base.css) para que el mapa siga a la paleta de cada versión.
    color: (getComputedStyle(document.documentElement).getPropertyValue('--rojo') || '').trim() || '#a3121d',
    // Dibujo de San Pablo para su marcador (V1: el SVG a pluma; V2: la acuarela). Lo fija data-ilu-san-pablo.
    iluSanPablo: el.getAttribute('data-ilu-san-pablo') || 'assets/ilustraciones/san-pablo.svg',
    semilla: 20270508,          // fija: el trazo «a mano» sale siempre igual (fecha de la boda)
    zoomMin: 13, zoomMax: 18, zoomMaxEncuadre: 16,
    zonas: {
      // Óvalo grande: San Pablo, Catedral, Plaza Mayor y Poniente quedan dentro con margen.
      recomendada: { centro: [41.65454, -4.72762], rx: 700, ry: 430, giro: 32 },
      // Óvalo pequeño: entre la Plaza del Poniente (vuelta del autocar) y la Plaza Mayor.
      comoda: { centro: [41.65265, -4.73008], rx: 270, ry: 150, giro: -24 }
    },
    // Rótulos de las zonas: posición en fracciones de los semiejes del óvalo [a lo largo, a lo ancho].
    rotulos: [
      { zona: 'recomendada', texto: 'Zona recomendada', pos: [0.15, -1.32], clase: 'mapa-rotulo--zona' },   // justo debajo del óvalo, al sur de la Catedral
      { zona: 'comoda', texto: '¡la más cómoda!', pos: [-0.55, -1.35], clase: 'mapa-rotulo--mano' }
    ],
    puntos: [
      {
        tipo: 'tarjeta', icono: 'san-pablo', lado: 'derecha',
        nombre: 'Iglesia de San Pablo', detalle: 'Ceremonia · 12:00 h',
        pos: [41.65710, -4.72442],
        destino: 'Iglesia de San Pablo, Plaza de San Pablo, 47011 Valladolid'
      },
      {
        tipo: 'tarjeta', icono: 'autocar', lado: 'arriba',
        nombre: 'Plaza del Poniente', detalle: 'Aquí os deja el autocar a la vuelta',
        pos: [41.65316, -4.73128],
        destino: 'Plaza del Poniente, Valladolid'
      },
      {
        tipo: 'etiqueta', icono: 'plaza', nombre: 'Plaza Mayor',
        detalle: 'El corazón del centro',
        pos: [41.65225, -4.72861],
        destino: 'Plaza Mayor, Valladolid'
      },
      {
        tipo: 'etiqueta', icono: 'catedral', nombre: 'Catedral',
        detalle: 'Al lado, el parking de la Plaza de Portugalete',
        pos: [41.65275, -4.72343],
        destino: 'Parking Plaza de Portugalete, Valladolid', textoRuta: 'Cómo llegar al parking'
      },
      { tipo: 'punto', nombre: 'Plaza de Zorrilla', pos: [41.64780, -4.72930] },
      { tipo: 'texto', nombre: 'Campo Grande', pos: [41.64560, -4.73080], clase: 'mapa-rotulo--parque' }
    ]
  };

  var TXT = {
    comoLlegar: '¿Cómo llegar?',
    seAbre: ' (se abre en Google Maps)',
    error: 'No hemos podido cargar el mapa:',
    errorEnlace: 'ábrelo en Google Maps'
  };

  var URL_ZONA = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent('Plaza Mayor, Valladolid');

  function urlRuta(destino) {
    return 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(destino);
  }

  /* ---------------------------------------------------------------------------------------
     Geometría: óvalo «a rotulador»
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

  // Punto a [este, norte] metros de c (lat, lng) → { lat, lng }.
  function desplazar(c, este, norte) {
    return {
      lat: c[0] + norte / 111320,
      lng: c[1] + este / (111320 * Math.cos(c[0] * Math.PI / 180))
    };
  }

  // Punto del óvalo z en fracciones de sus semiejes (u a lo largo, v a lo ancho), girado z.giro grados.
  function enOvalo(z, u, v) {
    var g = z.giro * Math.PI / 180, x = u * z.rx, y = v * z.ry;
    return desplazar(z.centro, x * Math.cos(g) - y * Math.sin(g), x * Math.sin(g) + y * Math.cos(g));
  }

  // Contorno ligeramente irregular (armónicos suaves, ≈ ±2 %) para que parezca trazado a mano.
  function ovaloARotulador(z, semilla) {
    var rnd = prng(semilla);
    var h = [[2, 0.008], [3, 0.007], [5, 0.004], [9, 0.0015]].map(function (p) {
      return { k: p[0], a: p[1] * (0.75 + 0.5 * rnd()), f: rnd() * TAU };
    });
    var inicio = rnd() * TAU, N = 120, pts = [];
    for (var i = 0; i < N; i++) {
      var t = inicio + (i / N) * TAU, s = 1;
      for (var j = 0; j < h.length; j++) s += h[j].a * Math.sin(h[j].k * t + h[j].f);
      pts.push(enOvalo(z, s * Math.cos(t), s * Math.sin(t)));
    }
    return pts;
  }

  /* ---------------------------------------------------------------------------------------
     Iconos a pluma (SVG en línea, con la paleta de la web)
     --------------------------------------------------------------------------------------- */
  var SPRITE = 'assets/ilustraciones/iconos.svg';
  var GLIFOS = {
    // Catedral: torre con chapitel y nave con puerta en arco
    catedral: '<path d="M14 34V17l3-4 3 4v17M17 13V8M15.5 9.5h3M20 34V22l8-5 8 5v12M10 34h28M25.5 34v-5a2.5 2.5 0 0 1 5 0v5"/>',
    // Plaza Mayor: soportales (arcos) bajo un friso
    plaza: '<path d="M9 15h30M10 15v19M38 15v19M9 34h30M10 34v-8a4.7 4.7 0 0 1 9.3 0v8M19.3 34v-8a4.7 4.7 0 0 1 9.4 0v8M28.7 34v-8a4.7 4.7 0 0 1 9.3 0v8M13 20.5h22"/>'
  };
  function icono(nombre) {
    if (nombre === 'san-pablo') {
      return '<img class="mapa-pin__ilu" src="' + CFG.iluSanPablo + '" alt="" decoding="async">';
    }
    var dentro = nombre === 'autocar'
      ? '<use href="' + SPRITE + '#autocar"/>'
      : GLIFOS[nombre];
    return '<span class="mapa-pin__chapa"><svg viewBox="0 0 48 48" aria-hidden="true" focusable="false" fill="none" ' +
      'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + dentro + '</svg></span>';
  }

  /* ---------------------------------------------------------------------------------------
     Carga perezosa de la API de Google
     --------------------------------------------------------------------------------------- */
  function cargarGoogle() {
    if (window.google && google.maps && google.maps.importLibrary) return Promise.resolve();
    return new Promise(function (ok, ko) {
      var cb = '__mapaGoogleListo';
      window[cb] = function () { delete window[cb]; ok(); };
      // Clave inválida o dominio no autorizado: Google llama a esta función global.
      window.gm_authFailure = function () { ko(new Error('auth')); mostrarError(); };
      var s = document.createElement('script');
      s.src = 'https://maps.googleapis.com/maps/api/js?' + [
        'key=' + encodeURIComponent(CFG.apiKey), 'v=weekly', 'loading=async',
        'language=es', 'region=ES', 'callback=' + cb
      ].join('&');
      s.async = true;
      s.onerror = function () { ko(new Error('js')); };
      document.head.appendChild(s);
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
    el.classList.remove('mapa--lista');
    var lienzo = el.querySelector('.mapa__lienzo');
    if (lienzo) lienzo.remove();
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
  function crearMapa(libs) {
    var g = google.maps;
    var Map = libs[0].Map, Polygon = libs[0].Polygon, Polyline = libs[0].Polyline, InfoWindow = libs[0].InfoWindow;
    var Marker = libs[1].AdvancedMarkerElement;

    var lienzo = document.createElement('div');
    lienzo.className = 'mapa__lienzo';
    el.appendChild(lienzo);

    var zR = CFG.zonas.recomendada, zC = CFG.zonas.comoda;
    var map = new Map(lienzo, {
      mapId: CFG.mapId,
      center: { lat: zR.centro[0], lng: zR.centro[1] }, zoom: 15,
      minZoom: CFG.zoomMin, maxZoom: CFG.zoomMax,
      disableDefaultUI: true, zoomControl: true,
      zoomControlOptions: { position: g.ControlPosition.INLINE_START_BLOCK_START },
      gestureHandling: 'cooperative', clickableIcons: false, keyboardShortcuts: true
    });

    /* Zona recomendada: relleno suave y borde continuo */
    var contornoR = ovaloARotulador(zR, CFG.semilla);
    new Polygon({
      map: map, paths: contornoR, clickable: false, zIndex: 1,
      fillColor: CFG.color, fillOpacity: 0.1, strokeColor: CFG.color, strokeOpacity: 0.9, strokeWeight: 2.5
    });

    /* Zona más cómoda: relleno algo más intenso y borde discontinuo (Polyline con guiones) */
    var contornoC = ovaloARotulador(zC, CFG.semilla + 1);
    new Polygon({
      map: map, paths: contornoC, clickable: false, zIndex: 2,
      fillColor: CFG.color, fillOpacity: 0.14, strokeOpacity: 0
    });
    new Polyline({
      map: map, path: contornoC.concat([contornoC[0]]), clickable: false, zIndex: 3, strokeOpacity: 0,
      icons: [{ icon: { path: 'M 0,-1 0,1', strokeColor: CFG.color, strokeOpacity: 0.9, strokeWeight: 2, scale: 3 }, offset: '0', repeat: '12px' }]
    });

    /* Rótulos de las zonas (no interactivos) */
    CFG.rotulos.forEach(function (r) {
      var span = document.createElement('span');
      span.className = 'mapa-rotulo ' + r.clase;
      span.textContent = r.texto;
      new Marker({
        map: map, position: enOvalo(CFG.zonas[r.zona], r.pos[0], r.pos[1]), content: span, zIndex: 5,
        // Si al alejar el mapa choca con una tarjeta o un icono, el rótulo se esconde (los lugares mandan).
        collisionBehavior: g.CollisionBehavior.OPTIONAL_AND_HIDES_LOWER_PRIORITY
      });
    });

    /* Puntos de referencia */
    var ventana = new InfoWindow({ maxWidth: 260 });
    CFG.puntos.forEach(function (p) {
      var c = document.createElement('div');
      c.className = 'mapa-pin mapa-pin--' + p.tipo + (p.lado ? ' mapa-pin--' + p.lado : '');
      if (p.tipo === 'tarjeta') {
        c.innerHTML = icono(p.icono) +
          '<span class="mapa-pin__tarjeta"><strong></strong><span></span></span>';
        c.querySelector('strong').textContent = p.nombre;
        c.querySelector('.mapa-pin__tarjeta span').textContent = p.detalle;
      } else if (p.tipo === 'etiqueta') {
        c.innerHTML = icono(p.icono) + '<span class="mapa-pin__nombre"></span>';
        c.querySelector('.mapa-pin__nombre').textContent = p.nombre;
      } else if (p.tipo === 'punto') {
        c.innerHTML = '<span class="mapa-pin__punto"></span><span class="mapa-pin__nombre"></span>';
        c.querySelector('.mapa-pin__nombre').textContent = p.nombre;
      } else {
        c.className = 'mapa-rotulo ' + (p.clase || '');
        c.textContent = p.nombre;
      }

      var conRuta = !!p.destino;
      var m = new Marker({
        map: map, position: { lat: p.pos[0], lng: p.pos[1] }, content: c,
        title: conRuta ? p.nombre + ' · ' + TXT.comoLlegar : '', gmpClickable: conRuta,
        collisionBehavior: g.CollisionBehavior.REQUIRED,
        zIndex: p.tipo === 'tarjeta' ? 30 : p.tipo === 'etiqueta' ? 20 : 10
      });
      if (!conRuta) return;

      m.addEventListener('gmp-click', function () {
        var v = document.createElement('div');
        v.className = 'mapa-popup';
        var t = document.createElement('strong'); t.className = 'mapa-popup__titulo'; t.textContent = p.nombre;
        var d = document.createElement('span'); d.className = 'mapa-popup__detalle'; d.textContent = p.detalle;
        var a = document.createElement('a'); a.className = 'boton'; a.href = urlRuta(p.destino);
        a.target = '_blank'; a.rel = 'noopener'; a.textContent = p.textoRuta || TXT.comoLlegar;
        var sr = document.createElement('span'); sr.className = 'sr-only'; sr.textContent = TXT.seAbre;
        a.appendChild(sr);
        v.appendChild(t); v.appendChild(d); v.appendChild(a);
        ventana.setContent(v);
        ventana.open({ map: map, anchor: m, shouldFocus: true });
      });
    });

    /* Encuadre: que se vea el óvalo grande entero (y lo vuelve a hacer al girar el móvil, si no se ha tocado) */
    var limites = new g.LatLngBounds();
    contornoR.forEach(function (pt) { limites.extend(pt); });
    // En el móvil el óvalo entero obliga a alejar tanto que los lugares se pisan: se encuadran los
    // lugares con «¿Cómo llegar?» y el óvalo puede salirse un poco por los bordes.
    var limitesMovil = new g.LatLngBounds();
    CFG.puntos.forEach(function (p) { if (p.destino) limitesMovil.extend({ lat: p.pos[0], lng: p.pos[1] }); });
    var tocado = false;
    var leyenda = document.querySelector('.mapa-leyenda');
    function margenes() {
      var m = { top: 16, right: 16, bottom: 16, left: 16 };
      // Pantalla ancha: la leyenda está encima del mapa, a la derecha; que no tape el óvalo.
      if (leyenda && getComputedStyle(leyenda).position === 'absolute') m.right = leyenda.offsetWidth + 32;
      // Móvil: las tarjetas van encima de su icono (sitio arriba) y los nombres debajo.
      if (esMovil()) m = { top: 64, right: 56, bottom: 48, left: 60 };
      return m;
    }
    function esMovil() { return lienzo.clientWidth < 600; }
    function encuadrar() {
      map.fitBounds(esMovil() ? limitesMovil : limites, margenes());
      g.event.addListenerOnce(map, 'idle', function () {
        if (map.getZoom() > CFG.zoomMaxEncuadre) map.setZoom(CFG.zoomMaxEncuadre);
      });
    }
    encuadrar();
    map.addListener('dragstart', function () { tocado = true; });
    lienzo.addEventListener('wheel', function () { tocado = true; }, { passive: true });
    var tRedim;
    window.addEventListener('resize', function () {
      clearTimeout(tRedim);
      tRedim = setTimeout(function () { if (!tocado) encuadrar(); }, 200);
    });

    el.classList.add('mapa--lista');
    el.setAttribute('data-mapa', 'listo');
    el.mapaGoogle = map;
    el.dispatchEvent(new CustomEvent('mapa:listo', { detail: { map: map } }));
  }

  /* ---------------------------------------------------------------------------------------
     Arranque
     --------------------------------------------------------------------------------------- */
  cuandoEstéCerca(function () {
    if (!CFG.apiKey) { mostrarError(); return; }
    el.setAttribute('data-mapa', 'cargando');
    cargarGoogle()
      .then(function () { return Promise.all([google.maps.importLibrary('maps'), google.maps.importLibrary('marker')]); })
      .then(crearMapa)
      .catch(function () { mostrarError(); });
  });
})();
