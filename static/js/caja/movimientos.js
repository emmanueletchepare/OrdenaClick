(function () {
    'use strict';

    let historialSolicitud = 0;

    function empresaActual() {
        const input = document.getElementById('empresaActiva');
        return input ? input.value : '';
    }

    function cajaElegida() {
        const selector = document.getElementById('cajaFiltroDisponibilidad');
        if (selector) { return selector.value; }
        const unica = document.querySelector('[data-caja-resumen]');
        return unica ? unica.dataset.cajaResumen : '';
    }

    function visibilidadCajas() {
        const selector = document.getElementById('cajaFiltroDisponibilidad');
        if (!selector) { return; }
        document.querySelectorAll('[data-caja-resumen]').forEach(function (seccion) {
            seccion.hidden = selector.value !== 'todas' && seccion.dataset.cajaResumen !== selector.value;
        });
    }

    function periodoHistorial() {
        const selector = document.getElementById('cajaHistorialModo');
        if (!selector) { return null; }
        const modo = selector.value;
        const contenedor = document.getElementById('cajaHistorialRango');
        if (contenedor) { contenedor.hidden = modo !== 'rango'; }
        const p = {modo: modo};
        if (modo === 'rango') {
            p.desde = document.getElementById('cajaHistorialDesde').value;
            p.hasta = document.getElementById('cajaHistorialHasta').value;
            if (!p.desde || !p.hasta) { return null; }
        }
        return p;
    }

    async function cargarHistorial(pagina) {
        const destino = document.getElementById('cajaHistorialResultados');
        if (!destino) { return; }
        const empresa = empresaActual();
        const caja = cajaElegida();
        const periodo = periodoHistorial();
        if (!empresa || !caja || !periodo) {
            destino.textContent = 'Seleccioná una Caja y fechas válidas para consultar los movimientos.';
            return;
        }
        const idSolicitud = ++historialSolicitud;
        destino.textContent = 'Consultando movimientos...';
        const params = new URLSearchParams({empresa: empresa, caja: caja, ...periodo});
        if (pagina) { params.set('pagina', String(pagina)); }
        try {
            const respuesta = await fetch('/caja/movimientos/historial/?' + params.toString(), {
                method: 'GET', credentials: 'same-origin', cache: 'no-store',
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            const datos = await respuesta.json();
            if (!respuesta.ok || !datos.ok) {
                throw new Error(datos.mensaje || 'No fue posible consultar los movimientos.');
            }
            if (idSolicitud === historialSolicitud && document.getElementById('cajaHistorialResultados') === destino) {
                destino.innerHTML = datos.html;
            }
        } catch (error) {
            if (idSolicitud === historialSolicitud && document.getElementById('cajaHistorialResultados') === destino) {
                destino.textContent = error.message;
            }
        }
    }

    async function abrirMovimientosCaja() {
        const actual = document.getElementById('cajaMovimientoFormulario');
        const empresa = actual ? actual.elements.empresa.value : empresaActual();
        const caja = actual ? actual.elements.caja.value : cajaElegida();
        if (!empresa || !caja || caja === 'todas') {
            window.alert('Seleccioná una Caja concreta antes de registrar movimientos.');
            return;
        }
        const contenido = document.getElementById('contenido-operativo');
        if (!contenido) { return; }
        try {
            const params = new URLSearchParams({empresa: empresa, caja: caja});
            const respuesta = await fetch('/caja/movimientos/?' + params.toString(), {
                method: 'GET', credentials: 'same-origin', cache: 'no-store',
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            const datos = await respuesta.json();
            if (!respuesta.ok || !datos.ok) { throw new Error(datos.mensaje || 'No fue posible consultar el formulario.'); }
            contenido.innerHTML = datos.html;
        } catch (error) {
            window.alert(error.message);
        }
    }

    async function guardarMovimiento(formulario) {
        const boton = document.getElementById('cajaMovGuardar');
        const mensaje = document.getElementById('cajaMovimientoMensaje');
        const otro = document.getElementById('cajaMovOtro');
        if (!boton || boton.disabled) { return; }
        boton.disabled = true;
        mensaje.textContent = 'Guardando movimiento...';
        const movimiento = {};
        for (const nombre of ['fecha', 'tipo', 'moneda', 'importe', 'concepto', 'clave_idempotencia']) {
            movimiento[nombre] = formulario.elements[nombre].value;
        }
        try {
            const respuesta = await fetch('/caja/movimientos/registrar/', {
                method: 'POST', credentials: 'same-origin', cache: 'no-store',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': formulario.elements.csrfmiddlewaretoken.value},
                body: JSON.stringify({empresa_id: formulario.elements.empresa.value,
                    caja_id: formulario.elements.caja.value, movimiento: movimiento})
            });
            const datos = await respuesta.json();
            if (!respuesta.ok || !datos.ok) { throw new Error(datos.mensaje || 'No fue posible registrar el movimiento.'); }
            mensaje.textContent = 'Movimiento registrado. Podés volver a Caja o registrar otro.';
            otro.hidden = false;
        } catch (error) {
            mensaje.textContent = error.message + ' Los datos permanecen en pantalla; podés reintentar.';
            boton.disabled = false;
        }
    }

    document.addEventListener('click', function (evento) {
        const accion = evento.target.closest('[data-caja-movimiento]');
        if (accion) {
            const tipo = accion.dataset.cajaMovimiento;
            if (tipo === 'abrir' || tipo === 'otro') { abrirMovimientosCaja(); }
            if (tipo === 'volver' && typeof window.mostrarCaja === 'function') { window.mostrarCaja(); }
            return;
        }
        const pagina = evento.target.closest('[data-caja-historial-pagina]');
        if (pagina) { cargarHistorial(pagina.dataset.cajaHistorialPagina); }
    });

    document.addEventListener('change', function (evento) {
        if (evento.target.id === 'cajaFiltroDisponibilidad') {
            visibilidadCajas(); cargarHistorial();
        }
        if (['cajaHistorialModo', 'cajaHistorialDesde', 'cajaHistorialHasta'].includes(evento.target.id)) {
            cargarHistorial();
        }
    });

    document.addEventListener('submit', function (evento) {
        if (evento.target.id === 'cajaMovimientoFormulario') {
            evento.preventDefault(); guardarMovimiento(evento.target);
        }
    });

    window.cargarHistorialCaja = function () { visibilidadCajas(); cargarHistorial(); };
})();
