/* Marta & Jorge · entrada de la portada: avance rápido, profundidad (parallax) y limpieza.
   La entrada en sí es CSS puro (css/intro.css); este fichero solo la acompaña. Sin dependencias. */
(() => {
  'use strict';

  const root = document.documentElement;
  const hero = document.getElementById('portada');
  if (!hero) return;
  const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const vista = root.classList.contains('intro-vista');
  const DURACION_MS = 6900; // pasado este tiempo la entrada ya ha terminado

  /* Pista para seguir bajando: se apaga en cuanto la persona hace scroll */
  const alBajar = () => hero.classList.toggle('scrolled', window.scrollY > 24);
  window.addEventListener('scroll', alBajar, { passive: true });
  alBajar();

  /* ---------- 0. Conexión lenta: las puertas no se abren hasta que la foto esté lista ---------- */
  const fotoHero = hero.querySelector('.ventana img');
  if (!reducir && !vista && fotoHero && !fotoHero.complete) {
    // tiempo que lleva sonando la entrada (todas las animaciones arrancan en el primer fotograma)
    const transcurrido = () => {
      try { return hero.getAnimations({ subtree: true }).reduce((m, a) => Math.max(m, a.currentTime || 0), 0); } catch (e) { return 0; }
    };
    // a los 3,1 s, justo antes de que empiecen las puertas (3,5 s), si la foto aún no ha llegado se espera a que llegue
    setTimeout(() => {
      if (fotoHero.complete) return;
      hero.classList.add('espera-foto');
      const seguir = () => hero.classList.remove('espera-foto');
      fotoHero.addEventListener('load', seguir, { once: true });
      fotoHero.addEventListener('error', seguir, { once: true });
      setTimeout(seguir, 9000); // pase lo que pase, no se espera más de 9 s
    }, Math.max(0, 3100 - transcurrido()));
  }

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
  const extra = hero.querySelector('.portada__extra');   // cuenta atrás y botón: se mueve igual que la foto para que esta no los pise
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
    // el efecto se detiene pronto (a los 450 px de scroll): así ninguna capa llega a pisar a otra ni a la sección siguiente
    const y = Math.max(0, Math.min(sy, 450)); // iOS: con el rebote al tirar hacia abajo scrollY es negativo
    // texto: sigue al scroll un poco más lento; foto y lo que va debajo (cuenta atrás, botón): aún más, y a la vez, para que no se
    // solapen; imagen dentro de la ventana: contra-movimiento
    texto.style.transform = `translate3d(${(curX * -5).toFixed(2)}px, ${(y * 0.08 + curY * -3).toFixed(2)}px, 0)`;
    foto.style.transform = `translate3d(${(curX * 7).toFixed(2)}px, ${(y * 0.16 + curY * 5).toFixed(2)}px, 0)`;
    if (extra) extra.style.transform = `translate3d(0, ${(y * 0.16).toFixed(2)}px, 0)`;
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
