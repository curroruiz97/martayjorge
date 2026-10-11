/* Se ejecuta en <head>, antes del primer pintado:
   · marca que hay JS (para los efectos de revelado) y, si main.js no arranca en 4 s, muestra todo igualmente;
   · hace esperar a la entrada hasta tener la imagen de los nombres (máximo 2,5 s);
   · decide si la entrada de la portada se reproduce: SIEMPRE, en cada carga de la página (se acelera con un toque o
     un scroll). Solo se omite con ?intro=0 o si el enlace lleva un ancla (p. ej. /#confirmacion), porque entonces
     la persona aterriza directamente en otra parte y la portada ni se ve. */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  window.__revealTimer = setTimeout(function () { root.classList.add('reveal-fallback'); }, 4000);
  try {
    if (/[?&]intro=0(&|$)/.test(location.search) || location.hash.length > 1) root.classList.add('intro-vista');
  } catch (e) {}
  // la entrada espera a la imagen de los nombres (js/intro.js la quita al tenerla), pero nunca más de 2,5 s
  if (!root.classList.contains('intro-vista')) {
    root.classList.add('espera-nombres');
    setTimeout(function () { root.classList.remove('espera-nombres'); }, 2500);
  }
})();
