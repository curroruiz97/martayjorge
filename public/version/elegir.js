/* Va en el <head> de la V2 (la portada, /), antes que nada. Mientras se comparan las dos versiones, quien llega sin
   haber elegido ve la V1 (la que había hasta ahora): se le lleva a /v1/. Con «V2» en el selector (o /?v=2) se queda
   aquí, y se recuerda. Para quitarlo cuando se decida: ver README («Versiones»). */
(function () {
  var v = null;
  var q = /[?&]v=(1|2)(?:&|$)/.exec(location.search);
  try {
    if (q) localStorage.setItem('mj-version', q[1]);
    v = q ? q[1] : localStorage.getItem('mj-version');
  } catch (e) { v = q ? q[1] : null; }
  if (v !== '2') location.replace('/v1/' + location.search + location.hash);
})();
