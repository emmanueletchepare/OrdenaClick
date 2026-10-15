/* OrdenaClick / Pendientes: menú de acciones; usa las operaciones y permisos existentes.
   El menú vive fuera de la tabla con scroll para no quedar recortado. */
(function () {
  'use strict';
  const bandeja = document.getElementById('bandejaPendientes');
  if (!bandeja) return;

  const menu = document.createElement('div');
  menu.className = 'gb-menu-desplegable';
  menu.id = 'gbMenuAcciones';
  menu.setAttribute('role', 'menu');
  menu.setAttribute('aria-label', 'Acciones del movimiento');
  menu.hidden = true;
  document.body.appendChild(menu);
  let disparador = null;
  const tablaDesplazable = bandeja.querySelector('.gb-tabla-contenedor');
  let scrollTablaAlAbrir = 0;
  let scrollPaginaAlAbrir = 0;

  function cerrar(restaurarFoco = false) {
    const anterior = disparador;
    menu.hidden = true;
    menu.replaceChildren();
    if (anterior && anterior.isConnected) {
      anterior.setAttribute('aria-expanded', 'false');
      if (restaurarFoco) anterior.focus({preventScroll: true});
    }
    disparador = null;
  }

  function accionesDe(celda) {
    return [...celda.querySelectorAll(':scope > button[data-confirmar-pendiente], :scope > button[data-revisar-pendiente], :scope > button[data-estado-echeq]')];
  }

  function preparar() {
    for (const celda of bandeja.querySelectorAll('.gb-tabla tbody td.gb-accion')) {
      if (celda.querySelector(':scope > .gb-abrir-acciones')) continue;
      if (accionesDe(celda).length === 0) continue;
      const boton = document.createElement('button');
      boton.type = 'button';
      boton.className = 'gb-btn gb-btn-menor gb-abrir-acciones';
      boton.textContent = '⋮';
      boton.title = 'Acciones del movimiento';
      boton.setAttribute('aria-label', 'Acciones del movimiento');
      boton.setAttribute('aria-haspopup', 'menu');
      boton.setAttribute('aria-expanded', 'false');
      boton.setAttribute('aria-controls', menu.id);
      celda.appendChild(boton);
      // Se ocultan con CSS solamente al estar listo el reemplazo.
      // Si falla JS, los botones originales siguen siendo usables.
      celda.classList.add('gb-acciones-preparadas');
    }
    if (disparador && !disparador.isConnected) cerrar();
  }

  function abrir(boton) {
    if (disparador === boton && !menu.hidden) {
      cerrar(true);
      return;
    }
    cerrar();
    const celda = boton.closest('td.gb-accion');
    if (!celda) return;
    const acciones = accionesDe(celda);
    if (acciones.length === 0) return;

    for (const original of acciones) {
      const opcion = document.createElement('button');
      opcion.type = 'button';
      opcion.className = 'gb-menu-opcion';
      opcion.setAttribute('role', 'menuitem');
      opcion.textContent = original.hasAttribute('data-confirmar-pendiente') ? 'Confirmar' : (original.hasAttribute('data-estado-echeq') ? 'Estado e historial' : original.textContent.trim());
      opcion.disabled = original.disabled;
      opcion.addEventListener('click', function () {
        cerrar();
        // Reusa la acción real; el JS bancario existente abre su modal,
        // manteniendo las validaciones y la autorización del servidor.
        original.click();
      });
      menu.appendChild(opcion);
    }

    disparador = boton;
    // Ignora eventos de scroll atrasados del posicionamiento automatico al pulsar.
    scrollTablaAlAbrir = tablaDesplazable ? tablaDesplazable.scrollTop : 0;
    scrollPaginaAlAbrir = window.scrollY;
    boton.setAttribute('aria-expanded', 'true');
    menu.hidden = false;
    const rect = boton.getBoundingClientRect();
    const margen = 8;
    // Dentro del panel, el iframe es alto pero sólo una fracción es visible.
    const limites = window.OrdenaClickPendientesAreaVisible
      ? window.OrdenaClickPendientesAreaVisible()
      : {top:0, bottom:window.innerHeight, left:0, right:window.innerWidth};
    menu.style.maxHeight = Math.max(80, Math.floor(limites.bottom - limites.top - 2*margen)) + 'px';
    const ancho = menu.offsetWidth;
    const alto = menu.offsetHeight;
    const minX = limites.left + margen;
    const maxX = Math.max(minX, limites.right - ancho - margen);
    const minY = limites.top + margen;
    const maxY = Math.max(minY, limites.bottom - alto - margen);
    const aIzquierda = rect.left - ancho - margen;
    const aDerecha = rect.right + margen;
    const izquierda = aIzquierda >= minX ? aIzquierda :
      (aDerecha + ancho <= limites.right - margen ? aDerecha : maxX);
    // Si no entra debajo de la fila, desplegar hacia arriba sin recortar.
    const y = rect.top + alto <= limites.bottom - margen ? rect.top : rect.bottom - alto;
    menu.style.left = Math.round(Math.max(minX, Math.min(maxX, izquierda))) + 'px';
    menu.style.top = Math.round(Math.max(minY, Math.min(maxY, y))) + 'px';
    menu.querySelector('button:not(:disabled)')?.focus({preventScroll: true});
  }

  bandeja.addEventListener('click', function (evento) {
    const boton = evento.target.closest('.gb-abrir-acciones');
    if (!boton || !bandeja.contains(boton)) return;
    abrir(boton);
  });
  document.addEventListener('click', function (evento) {
    if (evento.target.closest('.gb-abrir-acciones')) return;
    if (!menu.contains(evento.target)) cerrar();
  });
  document.addEventListener('keydown', function (evento) {
    if (menu.hidden) return;
    if (evento.key === 'Escape') {
      evento.preventDefault();
      cerrar(true);
    } else if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
      const botones = [...menu.querySelectorAll('button:not(:disabled)')];
      if (!botones.length) return;
      evento.preventDefault();
      const actual = botones.indexOf(document.activeElement);
      const siguiente = (actual + (evento.key === 'ArrowDown' ? 1 : -1) + botones.length) % botones.length;
      botones[siguiente].focus({preventScroll: true});
    }
  });
  window.addEventListener('scroll', function () {
    if (menu.hidden) return;
    const movioTabla = tablaDesplazable && tablaDesplazable.scrollTop !== scrollTablaAlAbrir;
    if (movioTabla || window.scrollY !== scrollPaginaAlAbrir) cerrar();
  }, true);
  window.addEventListener('resize', function () { if (!menu.hidden) cerrar(); });
  // Al desplazar el panel exterior, no dejar menús flotando sobre otras filas.
  try {
    const scrollPadre = window.frameElement && window.frameElement.closest('.main');
    if (scrollPadre) {
      const alDesplazar = () => { if (!menu.hidden) cerrar(); };
      scrollPadre.addEventListener('scroll', alDesplazar, {passive:true});
      window.addEventListener('pagehide', () => scrollPadre.removeEventListener('scroll', alDesplazar), {once:true});
    }
  } catch (_) { /* En vista independiente no hay panel externo. */ }
  const tbody = bandeja.querySelector('.gb-tabla tbody');
  if (tbody) new MutationObserver(preparar).observe(tbody, {childList: true});
  preparar();
})();
