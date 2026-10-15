/* Acceso al módulo bancario desde el panel operativo, sin JavaScript inline. */
(function () {
  'use strict';
  const formulario = document.getElementById('formEntrarGestionBancaria');
  if (!formulario) return;
  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    const boton = formulario.querySelector('button[type="submit"]');
    if (boton.disabled) return;
    boton.disabled = true;
    try {
      const respuesta = await fetch(formulario.action, {method:'POST',body:new FormData(formulario), credentials:'same-origin',redirect:'follow'});
      if (!respuesta.ok || !new URL(respuesta.url).pathname.startsWith('/gestion-bancaria/')) {
        throw new Error('El servidor no autorizó abrir Pendientes para esta Empresa.');
      }
      const contenedor = document.getElementById('contenido-operativo');
      if (!contenedor) throw new Error('No se encontró el panel operativo.');
      if (typeof limpiarPanelOperativo === 'function') limpiarPanelOperativo();
      const cuadro = document.createElement('iframe');
      cuadro.id = 'ocPendientesFrame';
      cuadro.title = 'Pendientes bancarios';
      cuadro.setAttribute('loading','eager');
      cuadro.setAttribute('scrolling','no');
      cuadro.width = '100%';
      cuadro.height = '1200';
      cuadro.className = 'oc-pendientes-frame';
      cuadro.src = '/gestion-bancaria/';
      contenedor.replaceChildren(cuadro);
    } catch (error) {
      alert(error.message || 'No se pudo abrir Pendientes.');
    } finally { boton.disabled = false; }
  });
  window.addEventListener('message', function (event) {
    const frame = document.getElementById('ocPendientesFrame');
    if (event.origin !== window.location.origin || !frame || event.source !== frame.contentWindow) return;
    if (event.data && event.data.tipo === 'oc-pendientes-alto' && Number.isFinite(event.data.alto)) {
      frame.height = String(Math.min(15000, Math.max(550, event.data.alto)));
    }
  });
})();
