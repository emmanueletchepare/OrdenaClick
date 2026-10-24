/* Navegación compartida: mismo sidebar, acciones existentes, un solo grupo abierto. */
(() => {
  'use strict';
  const menu = document.querySelector('.sidebar');
  if (!menu) return;
  const grupos = () => [...menu.querySelectorAll('details.oc-sidebar-grupo')];

  // El evento toggle de <details> no burbujea; capturarlo para cerrar los demás.
  // Las acciones usan el mismo sidebar. Solo varía la capacidad autorizada.
  // El modo restringido no carga panel_navegacion.js: ese script incluye
  // acciones administrativas que no deben exponerse al Colaborador.
  if (document.body.dataset.accesoRestringido === '1') {
    window.mostrarSubmenu = function () {
      document.getElementById('submenu-dinamico')?.replaceChildren();
      document.getElementById('contenido-operativo')?.replaceChildren();
    };
    window.mostrarABMGestionClaves = async function () {
      const empresa = document.getElementById('empresaActiva')?.value;
      const area = document.getElementById('contenido-operativo');
      if (!empresa || !area) return;
      try {
        const r = await fetch('/gestion-claves/?empresa=' + encodeURIComponent(empresa),
          {credentials:'same-origin',cache:'no-store'});
        const datos = await r.json();
        if (!r.ok || !datos.ok) throw new Error(datos.mensaje || 'No autorizado.');
        area.innerHTML = datos.html;
        if (typeof window.iniciarABMGestionClaves === 'function')
          window.iniciarABMGestionClaves();
      } catch (error) {
        alert(error.message || 'No se pudo cargar Gestión de claves.');
      }
    };
    window.volverDesdeGestionClaves = () => window.mostrarSubmenu();
  }

  // El antiguo mostrarSubmenu generaba una SEGUNDA botonera arriba del área operativa.
  // Se mantiene su contrato para retornos desde formularios, pero sin reconstruir
  // Registros, ABMs, Herramientas ni Configuración en otro lugar del panel.
  if (document.body.dataset.accesoRestringido !== '1' &&
      typeof window.mostrarSubmenu === 'function') {
    const original = window.mostrarSubmenu;
    window.mostrarSubmenu = function (tipo, ...resto) {
      if (!['registros', 'abms', 'herramientas', 'configuracion'].includes(tipo)) {
        return original.call(this, tipo, ...resto);
      }
      const alta = document.getElementById('bloque-alta-empresa');
      if (alta) alta.style.display = 'none';
      if (typeof window.restaurarCabeceraEmpresa === 'function')
        window.restaurarCabeceraEmpresa();
      document.getElementById('submenu-dinamico')?.replaceChildren();
      const contenido = document.getElementById('contenido-operativo');
      if (contenido) {
        contenido.classList.remove('oc-accesos-contenido');
        contenido.innerHTML = '<div class="empty-state">Elegí una opción desde el menú lateral.</div>';
      }
    };
  }

  // Un solo subítem seleccionado, con aria-current para accesibilidad.
  function marcarOpcion(boton) {
    menu.querySelectorAll('.oc-sidebar-hijos > button[aria-current]')
      .forEach(b => b.removeAttribute('aria-current'));
    if (boton && !boton.disabled) boton.setAttribute('aria-current', 'page');
  }

  function limpiarMenuSuperior() {
    if (document.getElementById('ocGestionAccesosFrame')) {
      if (typeof window.restaurarCabeceraEmpresa === 'function') window.restaurarCabeceraEmpresa();
      else {
        const titulo = document.getElementById('titulo-panel');
        if (titulo?.dataset.tituloEmpresa) titulo.textContent = titulo.dataset.tituloEmpresa;
      }
    }
    document.getElementById('submenu-dinamico')?.replaceChildren();
    document.getElementById('contenido-operativo')?.classList.remove('oc-accesos-contenido');
  }

  menu.addEventListener('toggle', event => {
    const actual = event.target;
    if (!actual.matches?.('details.oc-sidebar-grupo') || !actual.open) return;
    limpiarMenuSuperior();
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
    const opcion = elemento.closest('.oc-sidebar-hijos > button');
    if (opcion && !opcion.disabled) marcarOpcion(opcion);
    else if (!grupo) marcarOpcion(null);


    const gestion = elemento.dataset.ocGestionAccesosUrl;
    if (gestion) {
      event.preventDefault();
      const destino = document.getElementById('contenido-operativo');
      if (!destino) return;
      // La vista de acceso NO debe convivir con un formulario de Empresa abierto.
      const alta = document.getElementById('bloque-alta-empresa');
      if (alta) alta.style.display = 'none';
      const panel = document.getElementById('panel-empresa');
      if (panel) panel.style.display = 'block';
      limpiarMenuSuperior();
      destino.classList.add('oc-accesos-contenido');
      const frame = document.createElement('iframe');
      frame.id = 'ocGestionAccesosFrame';
      frame.title = 'Gestión de accesos';
      frame.src = gestion;
      frame.setAttribute('loading', 'eager');
      destino.replaceChildren(frame);
      const titulo = document.getElementById('titulo-panel');
      if (titulo) titulo.textContent = 'Gestión de accesos';
      const principal = document.querySelector('.main');
      if (principal) principal.scrollTop = 0;
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
    if (elemento.id === 'btnSidebarAlertas') {
      limpiarMenuSuperior();
      return;
    }
    if (!accion) return;
    event.preventDefault();
    if (accion.startsWith('vencimientos-')) {
      // Tres filtros exclusivos de Vencimientos; Alertas es otro módulo principal.
      const botones = {
        'vencimientos-hoy': 'btnVencimientosHoy',
        'vencimientos-semana': 'btnVencimientosSemana',
        'vencimientos-rango': 'btnVencimientosRango'
      };
      const id = botones[accion];
      if (!id) return;
      limpiarMenuSuperior();
      // Reutilizamos la vista, los eventos y las consultas ya implementados.
      // No se lanza una consulta previa a Alertas que pueda pisar el filtro elegido.
      if (!document.getElementById('tablaProximosVencimientos') ||
          document.querySelector('.vencimientos-contenedor[data-oc-vista="alertas"]')) {
        if (typeof window.construirEstructuraProximosVencimientos !== 'function' ||
            typeof window.conectarControlesProximosVencimientos !== 'function') return;
        window.construirEstructuraProximosVencimientos();
        window.conectarControlesProximosVencimientos();
      }
      document.getElementById(id)?.click();
      return;
    }
    if (accion === 'registros-comprobantes' || accion === 'registros-obligaciones') {
      limpiarMenuSuperior();
      // Módulos reales del Administrador, sin crear sus botones anteriores.
      const abrir = accion === 'registros-comprobantes'
        ? window.mostrarCargaSimple : window.mostrarObligaciones;
      if (typeof abrir === 'function') abrir();
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
      limpiarMenuSuperior();
      const nombre = funciones[accion.slice(4)];
      const funcion = nombre && window[nombre];
      if (typeof funcion === 'function') await funcion('menu');
      return;
    }
    if (accion === 'claves' && typeof window.mostrarABMGestionClaves === 'function') {
      limpiarMenuSuperior();
      await window.mostrarABMGestionClaves();
    }
    if (accion === 'modificar-empresa' && typeof window.mostrarModificarEmpresa === 'function') {
      window.mostrarModificarEmpresa();
    }
  });
})();
