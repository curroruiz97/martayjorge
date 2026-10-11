/* Selector de versión (V1 · V2) mientras los novios comparan las dos versiones de la web.
   · V1 (la que había) vive congelada en /v1/; V2 (la nueva) es la portada (/).
   · Los enlaces llevan ?v=1 / ?v=2: la página que se abre recuerda la elección (localStorage) y limpia la dirección.
   · Quien llega a / sin haber elegido ve la V1 (lo decide /version/elegir.js, en el <head> de la V2).
   Para quitarlo cuando se decida: ver README («Versiones»). */
(function () {
  'use strict';
  var CLAVE = 'mj-version';
  var esV1 = /^\/v1(\/|$)/.test(location.pathname);
  var q = /[?&]v=(1|2)(?:&|$)/.exec(location.search);
  if (q) {
    try { localStorage.setItem(CLAVE, q[1]); } catch (e) { /* modo privado: no se recuerda */ }
    try {
      var u = new URL(location.href);
      u.searchParams.delete('v');
      history.replaceState(history.state, '', u.pathname + u.search + u.hash);
    } catch (e) { /* navegador antiguo: se queda el ?v= */ }
  }
  function pintar() {
    var nav = document.createElement('nav');
    nav.className = 'mj-version';
    nav.setAttribute('aria-label', 'Versión de la web');
    [['1', '/v1/?v=1', 'V1', 'Versión 1 (la anterior)'], ['2', '/?v=2', 'V2', 'Versión 2 (la nueva)']].forEach(function (d) {
      var a = document.createElement('a');
      a.href = d[1];
      a.textContent = d[2];
      a.setAttribute('aria-label', d[3]);
      if ((d[0] === '1') === esV1) a.setAttribute('aria-current', 'page');
      nav.appendChild(a);
    });
    document.body.appendChild(nav);
  }
  if (document.body) pintar(); else document.addEventListener('DOMContentLoaded', pintar);
})();
