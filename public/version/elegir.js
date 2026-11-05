/* Va en el <head> de la V3 (la portada, /), antes que nada. Por defecto se ve la V3. Solo los enlaces antiguos que
   piden otra versión (/?v=1 o /?v=2) llevan a /v1/ o /v2/; ya no se recuerda ninguna elección.
   Para quitar el selector: ver README («Versiones»). */
(function () {
  var q = /[?&]v=(1|2)(?:&|$)/.exec(location.search);
  if (q) location.replace('/v' + q[1] + '/' + location.search + location.hash);
})();
