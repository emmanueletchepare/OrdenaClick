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
    if (Number.isFinite(alto) && alto >= 620 && alto <= 30000) {
      const nuevoAlto = String(Math.ceil(alto));
      if (frame.height !== nuevoAlto) frame.height = nuevoAlto;
    }
  });

  // Foto inmutable de la posición ANTES de que el ABM cambie el panel.
  // Capturar todos los ancestros, incluidos los que estaban en scroll=0:
  // el ABM puede desplazar luego un contenedor que inicialmente estaba arriba.
  function capturarPosicion(frame) {
    const contenedores = [];
    let nodo = frame.parentElement;
    while (nodo) {
      contenedores.push({nodo, arriba: nodo.scrollTop, izquierda: nodo.scrollLeft});
      nodo = nodo.parentElement;
    }
    const documento = document.scrollingElement;
    if (documento && !contenedores.some(p => p.nodo === documento)) {
      contenedores.push({nodo: documento, arriba: documento.scrollTop,
        izquierda: documento.scrollLeft});
    }
    return {contenedores, paginaX: window.scrollX, paginaY: window.scrollY,
      fichaY: frame.contentWindow?.scrollY || 0};
  }

  function restaurarPosicion(estado) {
    if (!estado.posicion) return;
    // Primero recuperar geometría externa. No enfocar controles del ABM.
    for (const posicion of estado.posicion.contenedores) {
      if (posicion.nodo.isConnected) {
        posicion.nodo.scrollTop = posicion.arriba;
        posicion.nodo.scrollLeft = posicion.izquierda;
      }
    }
    window.scrollTo(estado.posicion.paginaX, estado.posicion.paginaY);
    try { estado.frame.contentWindow.scrollTo(0, estado.posicion.fichaY); }
    catch (_) { /* iframe preservado, pero no accesible */ }
  }

  function restaurarPantalla(estado) {
    for (const [nombre, funcion] of Object.entries(estado.funcionesVolver)) {
      window[nombre] = funcion;
    }
    estado.abm.remove();
    estado.barra.remove();
    estado.contenido.id = 'contenido-operativo';
    estado.contenido.style.display = estado.displayAnterior;
    // Restaurar después de recuperar el DOM y después del ajuste de altura
    // del iframe. No mover ni recrear la ficha (podría perder adjuntos).
    restaurarPosicion(estado);
    requestAnimationFrame(() => {
      restaurarPosicion(estado);
      requestAnimationFrame(() => restaurarPosicion(estado));
    });
    setTimeout(() => restaurarPosicion(estado), 120);
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
      // La actualización del select puede alterar la altura de la ficha.
      requestAnimationFrame(() => restaurarPosicion(estado));
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
      posicion: capturarPosicion(frame),
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
