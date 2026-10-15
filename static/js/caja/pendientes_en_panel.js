/* Adapta el documento original a su contenedor, sin alterar lógica bancaria. */
(function () {
  'use strict';
  if (window.parent === window || !window.frameElement || window.frameElement.id !== 'ocPendientesFrame') return;
  document.body.classList.add('gb-en-panel');
  const marco = window.frameElement;
  const panel = marco.closest('.main') || window.parent.document.scrollingElement;

  // Las coordenadas pertenecen al iframe, pero los límites son la porción
  // visible del panel, no los miles de píxeles de alto del iframe.
  function areaVisible() {
    const f = marco.getBoundingClientRect();
    const p = panel.getBoundingClientRect();
    return {
      top: Math.max(0, Math.min(innerHeight, Math.max(0, p.top) - f.top)),
      bottom: Math.max(0, Math.min(innerHeight, Math.min(parent.innerHeight, p.bottom) - f.top)),
      left: Math.max(0, Math.min(innerWidth, Math.max(0, p.left) - f.left)),
      right: Math.max(0, Math.min(innerWidth, Math.min(parent.innerWidth, p.right) - f.left))
    };
  }

  let posicionAnterior = null;
  let habiaDialogo = false;
  const guardarPosicion = () => ({panel: panel.scrollTop, pagina: parent.scrollY, iframe: window.scrollY});
  function restaurarPosicion() {
    if (!posicionAnterior || !marco.isConnected) return;
    panel.scrollTop = posicionAnterior.panel;
    if (parent.scrollY !== posicionAnterior.pagina) parent.scrollTo(0, posicionAnterior.pagina);
    if (window.scrollY !== posicionAnterior.iframe) window.scrollTo(0, posicionAnterior.iframe);
  }

  function centrarDialogos() {
    const area = areaVisible();
    const alto = Math.max(110, area.bottom - area.top - 24);
    const ancho = Math.max(220, area.right - area.left - 24);
    for (const dialogo of document.querySelectorAll('.gb-dialog[open]')) {
      // Sólo geometría calculada; tipografía, colores y demás diseño en CSS.
      dialogo.style.top = Math.round((area.top + area.bottom) / 2) + 'px';
      dialogo.style.left = Math.round((area.left + area.right) / 2) + 'px';
      dialogo.style.maxHeight = Math.round(alto) + 'px';
      dialogo.style.maxWidth = Math.round(ancho) + 'px';
    }
  }

  // Se captura antes del clic que abre cualquier diálogo existente,
  // incluidos los botones originales reutilizados desde el menú flotante.
  document.addEventListener('click', function (evento) {
    if (evento.target.closest('.gb-menu-opcion, [data-confirmar-pendiente], [data-revisar-pendiente], [data-estado-echeq]')
        && !document.querySelector('.gb-dialog[open]')) {
      posicionAnterior = guardarPosicion();
    }
  }, true);

  function observarDialogos() {
    const abiertos = !!document.querySelector('.gb-dialog[open]');
    if (abiertos) {
      centrarDialogos();
      if (!habiaDialogo) {
        restaurarPosicion();
        requestAnimationFrame(restaurarPosicion);
      }
    } else if (habiaDialogo) {
      restaurarPosicion();
      requestAnimationFrame(restaurarPosicion);
      posicionAnterior = null;
    }
    habiaDialogo = abiertos;
  }
  new MutationObserver(observarDialogos).observe(document.documentElement, {
    subtree: true, attributes: true, attributeFilter: ['open']
  });
  panel.addEventListener('scroll', centrarDialogos, {passive:true});
  window.parent.addEventListener('resize', centrarDialogos);
  window.addEventListener('resize', centrarDialogos);
  window.addEventListener('pagehide', () => {
    panel.removeEventListener('scroll', centrarDialogos);
    window.parent.removeEventListener('resize', centrarDialogos);
  }, {once:true});
  window.OrdenaClickPendientesAreaVisible = areaVisible;
  function informar() {
    const alto = Math.max(550, Math.ceil(document.documentElement.scrollHeight));
    window.parent.postMessage({tipo:'oc-pendientes-alto',alto:alto}, window.location.origin);
  }
  window.addEventListener('load', informar);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(informar).observe(document.body);
  informar();
})();
