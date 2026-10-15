/* Adapta el documento original a su contenedor, sin alterar lógica bancaria. */
(function () {
  'use strict';
  if (window.parent === window || !window.frameElement || window.frameElement.id !== 'ocPendientesFrame') return;
  document.body.classList.add('gb-en-panel');
  function informar() {
    const alto = Math.max(550, Math.ceil(document.documentElement.scrollHeight));
    window.parent.postMessage({tipo:'oc-pendientes-alto',alto:alto}, window.location.origin);
  }
  window.addEventListener('load', informar);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(informar).observe(document.body);
  informar();
})();
