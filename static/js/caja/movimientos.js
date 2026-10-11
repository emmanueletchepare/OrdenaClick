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

    function abrirCorreccion(boton) {
        const panel = document.getElementById('cajaCorreccionForm');
        if (!panel) { return; }
        const form = panel.querySelector('form');
        const accion = boton.dataset.cajaCorr;
        form.elements.accion.value = accion;
        form.elements.movimiento_id.value = boton.dataset.movId;
        form.elements.caja.value = boton.dataset.movCaja;
        form.elements.clave.value = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : '';
        document.getElementById('cajaCorreccionTitulo').textContent = accion === 'Editar' ? 'Editar mediante corrección auditable' : 'Anular movimiento (no se borra el historial)';
        document.getElementById('cajaCorreccionCampos').hidden = accion !== 'Editar';
        if (accion === 'Editar') {
            for (const [nombre, valor] of Object.entries({
                tipo:boton.dataset.movTipo, moneda:boton.dataset.movMoneda,
                fecha:boton.dataset.movFecha, importe:boton.dataset.movImporte,
                concepto:boton.dataset.movConcepto
            })) { form.elements[nombre].value = valor || ''; }
        }
        form.elements.motivo.value = '';
        document.getElementById('cajaCorreccionMensaje').textContent = '';
        document.getElementById('cajaCorreccionGuardar').disabled = false;
        panel.hidden = false;
        form.elements.motivo.focus();
        panel.scrollIntoView({block:'nearest'});
    }

    async function guardarCorreccion(form) {
        const boton = document.getElementById('cajaCorreccionGuardar');
        if (boton.disabled) { return; }
        boton.disabled = true;
        const mensaje = document.getElementById('cajaCorreccionMensaje');
        mensaje.textContent = 'Guardando corrección...';
        const datos = {empresa_id:empresaActual(), caja_id:form.elements.caja.value,
            accion:form.elements.accion.value, motivo:form.elements.motivo.value,
            clave:form.elements.clave.value};
        if (datos.accion === 'Editar') {
            datos.nuevo = {};
            for (const nombre of ['fecha','tipo','moneda','importe','concepto']) {
                datos.nuevo[nombre] = form.elements[nombre].value;
            }
        }
        const filtro = {caja:cajaElegida(),
            modo:document.getElementById('cajaHistorialModo').value,
            desde:document.getElementById('cajaHistorialDesde').value,
            hasta:document.getElementById('cajaHistorialHasta').value};
        try {
            const respuesta = await fetch('/caja/movimientos/corregir/' + encodeURIComponent(form.elements.movimiento_id.value) + '/', {
                method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json',
                    'X-CSRFToken':form.elements.csrfmiddlewaretoken.value},body:JSON.stringify(datos)
            });
            const resultado = await respuesta.json();
            if (!respuesta.ok || !resultado.ok) { throw new Error(resultado.mensaje || 'No fue posible corregir el movimiento.'); }
            mensaje.textContent = 'Corrección registrada. Actualizando saldos e historial...';
            if (typeof window.mostrarCaja === 'function') {
                await window.mostrarCaja();
                const selector = document.getElementById('cajaFiltroDisponibilidad');
                if (selector && filtro.caja) { selector.value = filtro.caja; }
                document.getElementById('cajaHistorialModo').value = filtro.modo;
                document.getElementById('cajaHistorialDesde').value = filtro.desde;
                document.getElementById('cajaHistorialHasta').value = filtro.hasta;
                visibilidadCajas(); cargarHistorial();
            }
        } catch (error) {
            mensaje.textContent = error.message + ' Los datos ingresados siguen disponibles.';
            boton.disabled = false;
        }
    }

    document.addEventListener('click', function (evento) {
        const accion = evento.target.closest('[data-caja-corr]');
        if (accion) { abrirCorreccion(accion); return; }
        if (evento.target.closest('[data-caja-corr-cancelar]')) {
            const panel = document.getElementById('cajaCorreccionForm');
            if (panel) { panel.hidden = true; }
        }
    });
    document.addEventListener('submit', function (evento) {
        if (evento.target.id === 'formCorreccionCaja') {
            evento.preventDefault(); guardarCorreccion(evento.target);
        }
    });

    window.cargarHistorialCaja = function () { visibilidadCajas(); cargarHistorial(); };
})();
