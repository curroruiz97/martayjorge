/* Selector de versión (V1 · V2 · V3) mientras los novios comparan las versiones de la web.
   · V1 (la primera) vive congelada en /v1/, V2 en /v2/ y V3 (la nueva) es la portada (/).
   · Por defecto, en / se ve la V3. Los enlaces antiguos con ?v=1 / ?v=2 siguen llevando a esa versión
     (/version/elegir.js, en el <head> de la V3) y aquí solo se limpia el ?v= de la dirección.
   Para quitarlo cuando se decida: ver README («Versiones»). */
(function () {
  'use strict';
  var m = /^\/v([12])(\/|$)/.exec(location.pathname);
  var actual = m ? m[1] : '3';
  var q = /[?&]v=(1|2|3)(?:&|$)/.exec(location.search);
  if (q) {
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
    [['1', '/v1/', 'V1', 'Versión 1 (la primera)'], ['2', '/v2/', 'V2', 'Versión 2'], ['3', '/', 'V3', 'Versión 3 (la nueva)']].forEach(function (d) {
      var a = document.createElement('a');
      a.href = d[1];
      a.textContent = d[2];
      a.setAttribute('aria-label', d[3]);
      if (d[0] === actual) a.setAttribute('aria-current', 'page');
      nav.appendChild(a);
    });
    document.body.appendChild(nav);
  }
  if (document.body) pintar(); else document.addEventListener('DOMContentLoaded', pintar);
})();
