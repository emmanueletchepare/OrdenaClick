/* Herramientas → Nómina. Los ABM usan el MISMO panel y no destruyen la ficha. */
(() => {
  'use strict';
  let retorno = null;
  const ABMS = {
    centros: {campo: 'centro_operativo', abrir: 'mostrarABMCentrosOperativos', volver: 'volverDesdeABMCentrosOperativos'},
    recursos: {campo: 'vehiculo', abrir: 'mostrarABMRecursosOperativos', volver: 'volverDesdeABMRecursosOperativos'},
    bancos: {campo: 'banco', abrir: 'mostrarABMBancos', volver: 'volverDesdeABMBancos'},
  };

  function frameNomina() { return document.getElementById('ocNominaFrame'); }

  document.addEventListener('click', e => {
    const boton = e.target.closest('#btnNominaEmpleados');
    if (!boton) return;
    if (retorno) salirABM(false);
    const empresa = document.getElementById('empresaActiva')?.value;
    const destino = document.getElementById('contenido-operativo');
    if (!empresa || !destino) return;
    const frame = document.createElement('iframe');
    frame.id = 'ocNominaFrame';
    frame.title = 'Nómina de Empleados';
    frame.className = 'oc-nomina-frame';
    frame.width = '100%';
    frame.height = '1000';
    frame.setAttribute('loading', 'eager');
    frame.src = '/nomina/?empresa=' + encodeURIComponent(empresa);
    destino.replaceChildren(frame);
  });

  window.addEventListener('message', e => {
    if (e.origin !== location.origin || e.data?.tipo !== 'oc-nomina-alto') return;
    const frame = frameNomina();
    if (!frame || e.source !== frame.contentWindow) return;
    const alto = Number(e.data.alto);
    if (Number.isFinite(alto)) frame.height = String(Math.max(620, Math.min(15000, alto)));
  });

  function restaurarPantalla(estado) {
    for (const [nombre, funcion] of Object.entries(estado.funcionesVolver)) {
      window[nombre] = funcion;
    }
    estado.abm.remove();
    estado.barra.remove();
    estado.contenido.id = 'contenido-operativo';
    estado.contenido.style.display = estado.displayAnterior;
    const panel = document.querySelector('.main');
    if (panel) panel.scrollTop = estado.scrollPanel;
    window.scrollTo(0, estado.scrollPagina);
    try { estado.frame.contentWindow.scrollTo(0, estado.scrollFicha); } catch (_) { /* marco cerrado */ }
    requestAnimationFrame(() => {
      if (panel) panel.scrollTop = estado.scrollPanel;
      window.scrollTo(0, estado.scrollPagina);
      try { estado.frame.contentWindow.scrollTo(0, estado.scrollFicha); } catch (_) { /* marco cerrado */ }
    });
  }

  async function salirABM(seleccionar = true) {
    if (!retorno || retorno.cerrando) return;
    const estado = retorno;
    estado.cerrando = true;
    retorno = null;
    restaurarPantalla(estado);
    if (!seleccionar) return;
    try {
      const respuesta = await fetch('/nomina/empresa/' + encodeURIComponent(estado.empresa) + '/opciones/', {
        credentials: 'same-origin', cache: 'no-store',
      });
      if (!respuesta.ok) throw new Error('No se pudieron actualizar los selectores.');
      const datos = await respuesta.json();
      const opciones = datos[estado.campo];
      if (!datos.ok || !Array.isArray(opciones)) throw new Error('Respuesta de opciones inválida.');
      const nuevos = opciones.filter(o => !estado.antes.has(String(o.id)));
      const valorNuevo = nuevos.length === 1 ? String(nuevos[0].id) : null;
      estado.frame.contentWindow?.OrdenaClickNominaActualizarSelect?.(estado.campo, opciones, valorNuevo);
    } catch (error) {
      console.error('Nómina: opciones del ABM', error);
      alert('Volviste a Nómina, pero no se pudieron actualizar las opciones. Conservamos la ficha sin cambios.');
    }
  }

  window.OrdenaClickNominaAbrirABM = async function(tipo) {
    const opcion = ABMS[tipo];
    if (!opcion || retorno) return;
    const frame = frameNomina();
    const contenido = document.getElementById('contenido-operativo');
    const empresa = document.getElementById('empresaActiva')?.value;
    const abrir = window[opcion.abrir];
    if (!frame || !contenido || !empresa || typeof abrir !== 'function') {
      alert('No se pudo abrir el ABM. La ficha de Nómina permanece intacta.');
      return;
    }
    const select = frame.contentDocument?.querySelector('#nmFormulario [name="' + opcion.campo + '"]');
    if (!select) return;
    const panel = document.querySelector('.main');
    const barra = document.createElement('div');
    barra.className = 'oc-nomina-retorno';
    const boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'oc-nomina-retorno-boton';
    boton.textContent = '← Volver a ficha de empleado';
    boton.addEventListener('click', () => salirABM());
    barra.appendChild(boton);
    const host = document.createElement('div');
    const funcionesVolver = {};
    // Sólo interceptar el regreso del ABM abierto; respetar los niveles internos
    // (p. ej. Recurso → Centro) y su comportamiento LIFO ya aprobado.
    if (typeof window[opcion.volver] === 'function') {
      funcionesVolver[opcion.volver] = window[opcion.volver];
      window[opcion.volver] = () => salirABM();
    }
    retorno = {
      tipo, campo: opcion.campo, empresa, frame, contenido, barra, abm: host,
      displayAnterior: contenido.style.display,
      scrollPanel: panel ? panel.scrollTop : 0,
      scrollPagina: window.scrollY,
      scrollFicha: frame.contentWindow?.scrollY || 0,
      antes: new Set([...select.options].map(o => o.value).filter(Boolean)),
      funcionesVolver, cerrando: false,
    };
    // Preservar el iframe CONECTADO al DOM: moverlo lo recargaría y perdería archivos.
    contenido.id = 'oc-nomina-contenido-preservado';
    contenido.style.display = 'none';
    contenido.after(barra, host);
    host.id = 'contenido-operativo';
    try {
      await abrir('menu');
      if (!retorno) return;
      if (panel) panel.scrollTop = 0;
      window.scrollTo(0, 0);
    } catch (error) {
      console.error('Nómina: error abriendo ABM', error);
      await salirABM(false);
      alert('No se pudo abrir el ABM. La ficha de Nómina se conservó.');
    }
  };

  // Si el usuario sale a otro módulo, no dejar hosts temporales ni manejadores alterados.
  document.addEventListener('click', e => {
    if (retorno && e.target.closest('.sidebar-nav-btn')) salirABM(false);
  }, true);
})();
