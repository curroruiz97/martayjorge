/* Marta & Jorge · entrada de la portada: espera de la foto, avance rápido y limpieza.
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

  /* ---------- 0. Los nombres: la entrada espera a tener su imagen decodificada (boot.js pone el tope de 2,5 s) ---------- */
  if (root.classList.contains('espera-nombres')) {
    const listo = () => root.classList.remove('espera-nombres');
    const fin = hero.querySelector('.nombres__final');
    const src = fin && fin.getAttribute('href');
    if (!src) listo();
    else {
      const im = new Image();
      im.src = src;
      (im.decode ? im.decode() : Promise.reject(new Error('sin decode'))).then(listo, () => { im.complete ? listo() : im.addEventListener('load', listo, { once: true }); });
    }
  }

  /* ---------- 0b. Conexión lenta: las puertas no se abren hasta que la foto esté lista ---------- */
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
})();
