/* Marta & Jorge · entrada de la portada: avance rápido, profundidad (parallax) y limpieza.
   La entrada en sí es CSS puro (css/intro.css); este fichero solo la acompaña. Sin dependencias. */
(() => {
  'use strict';

  const root = document.documentElement;
  const hero = document.getElementById('portada');
  if (!hero) return;
  const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const vista = root.classList.contains('intro-vista');
  const DURACION_MS = 6200; // pasado este tiempo la entrada ya ha terminado

  /* ---------- 1. Avance rápido: si la persona hace scroll/toca/teclea durante la entrada, se acelera ---------- */
  let acelerada = false;
  const eventos = ['wheel', 'touchstart', 'pointerdown', 'keydown'];
  function acelerar() {
    if (acelerada) return;
    acelerada = true;
    quitarEscuchas();
    let anims = [];
    try { anims = hero.getAnimations({ subtree: true }); } catch (e) { return; }
    anims.forEach((a) => {
      try {
        if (a.effect.getComputedTiming().iterations === Infinity) return; // la «respiración» de la foto no se acelera
        a.updatePlaybackRate(7);
      } catch (e) { try { a.finish(); } catch (_) { /* nada */ } }
    });
  }
  function alScroll() { if (window.scrollY > 24) acelerar(); }
  function quitarEscuchas() {
    eventos.forEach((e) => window.removeEventListener(e, acelerar));
    window.removeEventListener('scroll', alScroll);
  }
  if (!reducir && !vista) {
    eventos.forEach((e) => window.addEventListener(e, acelerar, { passive: true }));
    window.addEventListener('scroll', alScroll, { passive: true });
  }
  setTimeout(() => { quitarEscuchas(); root.classList.add('intro-fin'); }, vista || reducir ? 0 : DURACION_MS);

  /* ---------- 2. Profundidad: capas a distinta velocidad con el scroll y, en escritorio, con el puntero ---------- */
  if (reducir) return;
  const texto = hero.querySelector('.portada__texto');
  const foto = hero.querySelector('.portada__foto');
  const dentro = hero.querySelector('.ventana__foto');
  if (!texto || !foto || !dentro) return;

  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  let sy = 0;              // scroll
  let objX = 0, objY = 0;  // puntero objetivo (-1..1)
  let curX = 0, curY = 0;  // puntero suavizado
  let pendiente = false;

  const limite = (v, m) => Math.max(-m, Math.min(m, v));

  function pintar() {
    pendiente = false;
    curX += (objX - curX) * 0.07;
    curY += (objY - curY) * 0.07;
    const y = Math.min(sy, window.innerHeight * 1.1);
    // texto: sigue al scroll un poco más lento; foto: aún más; imagen dentro de la ventana: contra-movimiento
    texto.style.transform = `translate3d(${(curX * -5).toFixed(2)}px, ${(y * 0.1 + curY * -3).toFixed(2)}px, 0)`;
    foto.style.transform = `translate3d(${(curX * 7).toFixed(2)}px, ${(y * 0.2 + curY * 5).toFixed(2)}px, 0)`;
    dentro.style.transform = `translate3d(${limite(curX * -9, 15).toFixed(2)}px, ${limite(y * 0.05 - curY * 7, 15).toFixed(2)}px, 0) scale(1.1)`;
    if (Math.abs(objX - curX) > 0.002 || Math.abs(objY - curY) > 0.002) solicitar();
  }
  function solicitar() { if (!pendiente) { pendiente = true; requestAnimationFrame(pintar); } }

  window.addEventListener('scroll', () => { sy = window.scrollY; solicitar(); }, { passive: true });
  if (finePointer) {
    window.addEventListener('pointermove', (e) => {
      if (e.pointerType && e.pointerType !== 'mouse') return;
      objX = (e.clientX / window.innerWidth - 0.5) * 2;
      objY = (e.clientY / window.innerHeight - 0.5) * 2;
      solicitar();
    }, { passive: true });
    document.addEventListener('mouseleave', () => { objX = 0; objY = 0; solicitar(); });
  }
  sy = window.scrollY;
  if (sy) solicitar();
})();
