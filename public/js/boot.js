/* Se ejecuta en <head>, antes del primer pintado:
   · marca que hay JS (para los efectos de revelado) y, si main.js no arranca en 4 s, muestra todo igualmente;
   · decide si la entrada de la portada se reproduce: una vez cada 12 horas por dispositivo, para que quien vuelva a
     abrir el enlace ese mismo día no tenga que verla otra vez (?intro=1 la fuerza, ?intro=0 la omite). */
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  window.__revealTimer = setTimeout(function () { root.classList.add('reveal-fallback'); }, 4000);
  try {
    var q = location.search, vista = false, ahora = Date.now();
    try {
      var ultima = Number(window.localStorage.getItem('mj-intro')) || 0;
      vista = ahora - ultima < 12 * 36e5;
      if (!vista) window.localStorage.setItem('mj-intro', String(ahora)); // se anota solo cuando se reproduce
    } catch (e) {
      // sin localStorage (modo privado…): al menos una vez por pestaña
      try { vista = sessionStorage.getItem('mj-intro') === '1'; sessionStorage.setItem('mj-intro', '1'); } catch (e2) {}
    }
    if (/[?&]intro=0(&|$)/.test(q)) vista = true;
    if (/[?&]intro=1(&|$)/.test(q)) vista = false;
    if (vista) root.classList.add('intro-vista');
  } catch (e) {}
})();
