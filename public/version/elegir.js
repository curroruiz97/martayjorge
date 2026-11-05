/* Va en el <head> de la V3 (la portada, /), antes que nada. Mientras se comparan las versiones, quien llega sin
   haber elegido ve la V1 (la que había al principio): se le lleva a /v1/. Con «V2» en el selector (o /?v=2) se le
   lleva a /v2/ y con «V3» (o /?v=3) se queda aquí; la elección se recuerda. Para quitarlo: ver README («Versiones»). */
(function () {
  var v = null;
  var q = /[?&]v=(1|2|3)(?:&|$)/.exec(location.search);
  try {
    if (q) localStorage.setItem('mj-version', q[1]);
    v = q ? q[1] : localStorage.getItem('mj-version');
  } catch (e) { v = q ? q[1] : null; }
  if (v !== '3') location.replace((v === '2' ? '/v2/' : '/v1/') + location.search + location.hash);
})();
