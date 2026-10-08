/* Se ejecuta en <head>, antes del primer pintado: marca que hay JS (para los
   efectos de revelado) y, si main.js no arranca en 4 s, muestra todo igualmente. */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  window.__revealTimer = setTimeout(function () { root.classList.add('reveal-fallback'); }, 4000);
})();
