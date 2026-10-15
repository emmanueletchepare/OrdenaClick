/* Cartera virtual e-Cheq: interfaz de estados e historial, sin autoridad financiera. */
(function () {
  'use strict';
  const modal = document.getElementById('gbModalEstadoEcheq');
  const formulario = document.getElementById('gbFormEstadoEcheq');
  if (!modal || !formulario) return;
  const mensaje = document.getElementById('gbEstadoMensaje');
  const selector = formulario.elements.estado;
  const fecha = formulario.elements.fecha;
  const descripcion = document.getElementById('gbEstadoInstrumento');
  const actual = document.getElementById('gbEstadoActual');
  const historial = document.getElementById('gbEstadoHistorial');
  const guardar = document.getElementById('gbGuardarEstado');
  let instrumentoId = null;
  let cargando = false;

  function informar(texto) { mensaje.textContent = texto; }
  function urlDetalle(id) { return '/gestion-bancaria/echeq/' + encodeURIComponent(id) + '/estado/'; }
  function urlGuardar(id) { return '/gestion-bancaria/echeq/' + encodeURIComponent(id) + '/registrar-estado/'; }
  function rellenar(data) {
    descripcion.textContent = 'e-Cheq ' + data.instrumento + ' · ' + data.titular;
    actual.textContent = data.estado_texto;
    selector.replaceChildren();
    const neutra = new Option('Seleccionar acción', '');
    selector.appendChild(neutra);
    for (const nombre of data.acciones) selector.appendChild(new Option(nombre, nombre));
    guardar.disabled = data.acciones.length === 0;
    fecha.max = data.fecha_hoy;
    fecha.value = data.fecha_hoy;
    formulario.elements.observaciones.value = '';
    historial.replaceChildren();
    for (const evento of data.historial) {
      const fila = document.createElement('tr');
      for (const columna of ['fecha','accion','usuario','detalle']) {
        const td = document.createElement('td');
        td.textContent = evento[columna] || '—';
        fila.appendChild(td);
      }
      historial.appendChild(fila);
    }
    if (!data.historial.length) {
      const fila = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 4;
      td.textContent = 'Sin eventos registrados.';
      fila.appendChild(td);
      historial.appendChild(fila);
    }
  }
  async function cargar(id) {
    const response = await fetch(urlDetalle(id), {credentials: 'same-origin', cache: 'no-store'});
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.mensaje || 'No se pudo cargar el historial.');
    rellenar(data);
  }
  document.addEventListener('click', function (evento) {
    const origen = evento.target.closest('button[data-estado-echeq]');
    if (!origen) return;
    const id = origen.dataset.estadoEcheq;
    if (!/^\d+$/.test(id)) return;
    instrumentoId = id;
    informar('Cargando historial...');
    historial.replaceChildren();
    guardar.disabled = true;
    modal.showModal();
    cargar(id).then(() => informar('')).catch(error => informar(error.message));
  });
  document.getElementById('gbCerrarEstado').addEventListener('click', () => modal.close());
  formulario.addEventListener('input', function (ev) {
    if (!cargando && ev.target.name !== 'clave') formulario.elements.clave.value = '';
  });
  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    if (!instrumentoId || cargando || !formulario.reportValidity() || !selector.value) return;
    if (!window.crypto || !window.crypto.randomUUID) {
      informar('Este navegador no admite identificadores seguros.');
      return;
    }
    cargando = true;
    guardar.disabled = true;
    informar('Registrando acción...');
    if (!formulario.elements.clave.value) formulario.elements.clave.value = window.crypto.randomUUID();
    try {
      const response = await fetch(urlGuardar(instrumentoId), {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        body: new FormData(formulario),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.mensaje || 'No se pudo registrar la acción.');
      await cargar(instrumentoId);
      formulario.elements.clave.value = '';
      informar('Acción registrada y auditada.');
    } catch (error) {
      informar(error.message || 'Error de conexión. Verificá el historial antes de reintentar.');
    } finally { cargando = false; }
  });
})();
