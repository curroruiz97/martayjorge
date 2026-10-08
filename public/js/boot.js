/* Se ejecuta en <head>, antes del primer pintado:
   · marca que hay JS (para los efectos de revelado) y, si main.js no arranca en 4 s, muestra todo igualmente;
   · decide si la entrada de la portada se reproduce: solo la primera vez por sesión (?intro=1 la fuerza, ?intro=0 la omite). */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  window.__revealTimer = setTimeout(function () { root.classList.add('reveal-fallback'); }, 4000);
  try {
    var q = location.search, vista = false;
    try { vista = sessionStorage.getItem('mj-intro') === '1'; sessionStorage.setItem('mj-intro', '1'); } catch (e) {}
    if (/[?&]intro=0(&|$)/.test(q)) vista = true;
    if (/[?&]intro=1(&|$)/.test(q)) vista = false;
    if (vista) root.classList.add('intro-vista');
  } catch (e) {}
})();
