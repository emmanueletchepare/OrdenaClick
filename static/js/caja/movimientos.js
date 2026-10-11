(function () {
    'use strict';

    function contextoCajaActual() {
        const empresa = document.getElementById('empresaActiva');
        const selector = document.getElementById('cajaFiltroDisponibilidad');
        const unica = document.querySelector('[data-caja-resumen]');
        const caja = selector ? (selector.value === 'todas' ? '' : selector.value) :
            (unica ? unica.dataset.cajaResumen : '');
        return { empresa: empresa ? empresa.value : '', caja: caja || '' };
    }

    function parametros(contexto, pagina) {
        const query = new URLSearchParams({empresa: contexto.empresa, caja: contexto.caja});
        if (pagina) { query.set('pagina', String(pagina)); }
        return query.toString();
    }

    async function obtenerPantalla(contexto, pagina) {
        const respuesta = await fetch('/caja/movimientos/?' + parametros(contexto, pagina), {
            method: 'GET', credentials: 'same-origin', cache: 'no-store',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const datos = await respuesta.json();
        if (!respuesta.ok || !datos.ok) {
            throw new Error(datos.mensaje || 'No fue posible consultar los movimientos.');
        }
        return datos.html;
    }

    async function abrirMovimientosCaja() {
        const formularioActual = document.getElementById('cajaMovimientoFormulario');
        const contexto = formularioActual ? {
            empresa: formularioActual.elements.empresa.value,
            caja: formularioActual.elements.caja.value
        } : contextoCajaActual();
        if (!contexto.empresa || !contexto.caja) {
            window.alert('Seleccioná una Caja concreta antes de registrar movimientos.');
            return;
        }
        const contenido = document.getElementById('contenido-operativo');
        if (!contenido) { return; }
        // Mantener la pantalla actual hasta que el servidor autorice la Caja.
        try {
            const html = await obtenerPantalla(contexto);
            contenido.innerHTML = html;
        } catch (error) {
            window.alert(error.message);
        }
    }

    async function actualizarHistorial(pagina) {
        const form = document.getElementById('cajaMovimientoFormulario');
        const destino = document.getElementById('cajaMovimientosHistorial');
        if (!form || !destino) { return; }
        const contexto = {
            empresa: form.elements.empresa.value, caja: form.elements.caja.value
        };
        try {
            const html = await obtenerPantalla(contexto, pagina);
            const fragmento = new DOMParser().parseFromString(html, 'text/html');
            const historial = fragmento.getElementById('cajaMovimientosHistorial');
            if (!historial) { throw new Error('No se recibió el historial.'); }
            destino.innerHTML = historial.innerHTML;
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
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formulario.elements.csrfmiddlewaretoken.value
                },
                body: JSON.stringify({
                    empresa_id: formulario.elements.empresa.value,
                    caja_id: formulario.elements.caja.value,
                    movimiento: movimiento
                })
            });
            const datos = await respuesta.json();
            if (!respuesta.ok || !datos.ok) {
                throw new Error(datos.mensaje || 'No fue posible registrar el movimiento.');
            }
            mensaje.textContent = 'Movimiento registrado. Podés volver a Caja o registrar otro.';
            otro.hidden = false;
            // La clave del formulario ya se consumió; impedir otra operación distinta con ella.
            return;
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
            if (tipo === 'volver' && typeof window.mostrarCaja === 'function') {
                window.mostrarCaja();
            }
            return;
        }
        const botonPagina = evento.target.closest('[data-caja-mov-pagina]');
        if (botonPagina) { actualizarHistorial(botonPagina.dataset.cajaMovPagina); }
    });

    document.addEventListener('submit', function (evento) {
        if (evento.target.id === 'cajaMovimientoFormulario') {
            evento.preventDefault();
            guardarMovimiento(evento.target);
        }
    });
})();
