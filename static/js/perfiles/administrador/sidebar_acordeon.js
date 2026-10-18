/* Navegación compartida: mismo sidebar, acciones existentes, un solo grupo abierto. */
(() => {
  'use strict';
  const menu = document.querySelector('.sidebar');
  if (!menu) return;
  const grupos = () => [...menu.querySelectorAll('details.oc-sidebar-grupo')];

  // El evento toggle de <details> no burbujea; capturarlo para cerrar los demás.
  menu.addEventListener('toggle', event => {
    const actual = event.target;
    if (!actual.matches?.('details.oc-sidebar-grupo') || !actual.open) return;
    grupos().forEach(g => { if (g !== actual) g.open = false; });
  }, true);

  menu.addEventListener('click', async event => {
    const elemento = event.target.closest('button, a, summary');
    if (!elemento || !menu.contains(elemento)) return;
    const grupo = elemento.closest('details.oc-sidebar-grupo');
    // Solo la navegación principal cierra su grupo activo; las hojas no lo hacen.
    if (!grupo && (elemento.matches('[data-sidebar-item], a.sidebar-nav-btn') || elemento.closest('form.sidebar-pendientes-empresa'))) {
      grupos().forEach(g => { g.open = false; });
    }
    if (elemento.matches('summary')) return;

    const gestion = elemento.dataset.ocGestionAccesosUrl;
    if (gestion) {
      event.preventDefault();
      const destino = document.getElementById('contenido-operativo');
      if (!destino) return;
      const frame = document.createElement('iframe');
      frame.id = 'ocGestionAccesosFrame';
      frame.title = 'Gestión de accesos';
      frame.src = gestion;
      destino.replaceChildren(frame);
      const submenu = document.getElementById('submenu-dinamico');
      if (submenu) submenu.replaceChildren();
      let observador = null;
      frame.addEventListener('load', () => {
        observador?.disconnect();
        const ajustar = () => {
          if (!frame.isConnected) { observador?.disconnect(); return; }
          try {
            const doc = frame.contentDocument;
            if (!doc) return;
            const contenido = doc.querySelector('.gb-contenedor');
            if (!contenido) return;
            // El alto natural del contenido no depende del alto del iframe.
            const alto = Math.max(640, Math.ceil(contenido.scrollHeight) + 24);
            const objetivo = Math.min(30000, alto) + 'px';
            if (frame.style.height !== objetivo) frame.style.height = objetivo;
          } catch (_) { /* no se amplía el acceso a otros orígenes */ }
        };
        ajustar();
        if (typeof ResizeObserver !== 'undefined' && frame.contentDocument?.body) {
          observador = new ResizeObserver(ajustar);
          observador.observe(frame.contentDocument.body);
        }
      });
      return;
    }

    const accion = elemento.dataset.ocSidebarAccion;
    if (!accion) return;
    event.preventDefault();
    if (accion === 'registros-comprobantes' || accion === 'registros-obligaciones') {
      if (typeof window.mostrarSubmenu !== 'function') return;
      window.mostrarSubmenu('registros');
      const id = accion === 'registros-comprobantes' ? 'btnRegistrosComprobantes' : 'btn-obligaciones';
      document.getElementById(id)?.click();
      return;
    }
    const funciones = {
      centros:'mostrarABMCentrosOperativos', recursos:'mostrarABMRecursosOperativos',
      proveedores:'mostrarABMProveedores', tipos:'mostrarABMTiposGasto',
      clientes:'mostrarABMClientes', bancos:'mostrarABMBancos',
      cuentas:'mostrarABMCuentasBancarias', tarjetas:'mostrarABMTarjetas',
      retenciones:'mostrarABMRetenciones'
    };
    if (accion.startsWith('abm-')) {
      const nombre = funciones[accion.slice(4)];
      const funcion = nombre && window[nombre];
      if (typeof funcion === 'function') await funcion('menu');
      return;
    }
    if (accion === 'claves' && typeof window.mostrarABMGestionClaves === 'function') {
      await window.mostrarABMGestionClaves();
    }
    if (accion === 'modificar-empresa' && typeof window.mostrarModificarEmpresa === 'function') {
      window.mostrarModificarEmpresa();
    }
  });
})();
