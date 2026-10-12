(function () {
    'use strict';
    const lotes = {bancos: [], echeqs: []};
    const edicion = {bancos: null, echeqs: null};
    let guardando = false;
    const $ = (selector, base=document) => base.querySelector(selector);
    const campos = {
        bancos: ['tipo', 'fecha', 'identificacion', 'importe'],
        echeqs: ['titular', 'numero', 'codigo_banco', 'banco', 'importe', 'acreditacion', 'condicion']
    };
    function formatoImporte(valor) {
        const texto = String(valor).trim();
        const normal = texto.includes(',') ? texto.replace(/\./g, '').replace(',', '.') :
            (/^\d{1,3}(?:\.\d{3})+$/.test(texto) ? texto.replace(/\./g, '') : texto);
        const n = Number(normal);
        // Preservar formatos de entrada; el servidor valida el importe al guardar.
        return Number.isFinite(n) ? n.toLocaleString('es-AR', {minimumFractionDigits:2, maximumFractionDigits:2}) : String(valor);
    }
    function nuevoId() {
        if (crypto && typeof crypto.randomUUID === 'function') return crypto.randomUUID();
        const bytes = new Uint8Array(16);
        crypto.getRandomValues(bytes);
        bytes[6] = (bytes[6] & 15) | 64;
        bytes[8] = (bytes[8] & 63) | 128;
        const h = Array.from(bytes).map(x => x.toString(16).padStart(2, '0')).join('');
        return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
    }
    function elemento(tag, text, cls) {
        const el = document.createElement(tag);
        if (text !== undefined && text !== null) el.textContent = text;
        if (cls) el.className = cls;
        return el;
    }
    function llenarFormulario(clase, fila) {
        const form = $('#gbCarga' + (clase === 'bancos' ? 'Bancos' : 'Echeqs'));
        for (const campo of campos[clase]) form.elements[campo].value = fila[campo] || '';
        const boton = $('[data-agregar]', form);
        if (boton) boton.textContent = 'Actualizar fila';
        form.elements.importe.focus();
    }
    function render(clase) {
        const tabla = $(clase === 'bancos' ? '#gbListaBancos' : '#gbListaEcheqs');
        tabla.replaceChildren();
        const ncols = clase === 'bancos' ? 4 : 5;
        if (!lotes[clase].length) {
            const fila = elemento('tr'); const celda = elemento('td', 'Sin movimientos agregados.', 'gb-vacio');
            celda.colSpan = ncols; fila.append(celda); tabla.append(fila);
        }
        lotes[clase].forEach((item, indice) => {
            const tr = elemento('tr');
            const datos = clase === 'bancos' ? [
                item.fecha, item.identificacion || 'Sin identificar', `$ ${formatoImporte(item.importe)}`
            ] : [
                `${item.numero} · ${item.titular}`, item.banco,
                item.condicion === 'NoOrden' ? 'No a la orden' : 'A la orden',
                `$ ${formatoImporte(item.importe)}`
            ];
            datos.forEach((v, i) => tr.append(elemento('td', v, i === datos.length - 1 ? 'gb-numero' : '')));
            const td = elemento('td', null, 'gb-accion');
            for (const [accion, icono, titulo] of [['editar', '✎', 'Editar fila'], ['eliminar', '×', 'Eliminar fila']]) {
                const b = elemento('button', icono, 'gb-icono');
                b.type = 'button'; b.title = titulo; b.setAttribute('aria-label', titulo);
                b.dataset.accionFila = accion; b.dataset.clase = clase; b.dataset.indice = String(indice);
                td.append(b);
            }
            tr.append(td); tabla.append(tr);
        });
        const guardar = $(`[data-guardar-lote="${clase}"]`);
        guardar.disabled = lotes[clase].length === 0 || guardando;
    }
    function agregar(clase, form) {
        const fila = {};
        for (const campo of campos[clase]) fila[campo] = form.elements[campo].value.trim();
        // El nombre del cliente es optativo al detectar el ingreso.
        if (edicion[clase] === null) {
            fila.clave = nuevoId(); lotes[clase].push(fila);
        } else {
            fila.clave = lotes[clase][edicion[clase]].clave;
            lotes[clase][edicion[clase]] = fila;
            edicion[clase] = null;
        }
        // La cuenta no se borra; se comparte entre todas las filas del lote.
        for (const campo of campos[clase]) {
            if (campo === 'fecha') continue;
            if (campo === 'condicion') {form.elements[campo].value = 'Orden'; continue;}
            if (campo === 'tipo') {form.elements[campo].value = 'Transferencia'; continue;}
            form.elements[campo].value = '';
        }
        const boton = $('[data-agregar]', form);
        if (boton) boton.textContent = 'Agregar';
        $(`[data-mensaje-lote="${clase}"]`).textContent = '';
        render(clase);
    }
    async function actualizarBandeja() {
        try {
            const r = await fetch(window.location.href, {credentials:'same-origin',cache:'no-store'});
            if (!r.ok) return;
            const html = new DOMParser().parseFromString(await r.text(), 'text/html');
            const tablaNueva = $('#bandejaPendientes .gb-tabla tbody', html);
            const tablaActual = $('#bandejaPendientes .gb-tabla tbody');
            if (tablaNueva && tablaActual) tablaActual.replaceChildren(...Array.from(tablaNueva.children));
        } catch (_) { /* Confirmado el guardado: no esconder éxito si falla recarga visual. */ }
    }
    async function guardar(clase) {
        if (guardando || !lotes[clase].length) return;
        const form = $('#gbCarga' + (clase === 'bancos' ? 'Bancos' : 'Echeqs'));
        const cuenta = form.elements.cuenta.value;
        const mensaje = $(`[data-mensaje-lote="${clase}"]`);
        if (!cuenta) {mensaje.textContent = 'Seleccioná la cuenta bancaria antes de guardar.'; return;}
        guardando = true; render(clase); mensaje.textContent = 'Guardando el lote...';
        try {
            const response = await fetch('/gestion-bancaria/lote/', {
                method:'POST', credentials:'same-origin', cache:'no-store',
                headers:{'Content-Type':'application/json','X-CSRFToken':form.elements.csrfmiddlewaretoken.value},
                body:JSON.stringify({clase, cuenta, filas:lotes[clase]})
            });
            const data = await response.json();
            if (!response.ok || !data.ok) throw new Error(data.mensaje || 'No se pudo guardar el lote.');
            lotes[clase] = []; edicion[clase] = null;
            mensaje.textContent = `${data.ids.length} movimiento(s) guardados correctamente.`;
            render(clase);
            await actualizarBandeja();
        } catch (error) {
            mensaje.textContent = error.message + ' El lote permanece en pantalla para reintentar.';
        } finally {guardando=false; render(clase);}
    }
    for (const clase of ['bancos','echeqs']) {
        const form = $('#gbCarga' + (clase === 'bancos' ? 'Bancos' : 'Echeqs'));
        if (form) form.addEventListener('submit', ev => {ev.preventDefault(); if(form.reportValidity()) agregar(clase, form);});
    }
    document.addEventListener('change', ev => {
        if (ev.target.matches('.gb-filtro select')) ev.target.form.submit();
    });
    document.addEventListener('click', ev => {
        const tab = ev.target.closest('[data-tipo-carga]');
        if (tab) {
            const clase = tab.dataset.tipoCarga;
            document.querySelectorAll('[data-pantalla-carga]').forEach(p => p.hidden = p.dataset.pantallaCarga !== clase);
            document.querySelectorAll('[data-tipo-carga]').forEach(p => p.classList.toggle('activa', p === tab));
        }
        const accion = ev.target.closest('[data-accion-fila]');
        if (accion) {
            const clase = accion.dataset.clase, indice = Number(accion.dataset.indice);
            if (!lotes[clase][indice] || guardando) return;
            if (accion.dataset.accionFila === 'editar') {
                edicion[clase] = indice; llenarFormulario(clase, lotes[clase][indice]);
            } else {
                lotes[clase].splice(indice, 1);
                if (edicion[clase] !== null) edicion[clase] = null;
                render(clase);
            }
        }
        const guardarBtn = ev.target.closest('[data-guardar-lote]');
        if (guardarBtn) guardar(guardarBtn.dataset.guardarLote);
        const confirmar = ev.target.closest('[data-confirmar-pendiente]');
        if (confirmar) {
            const dialogo = $('#gbModalResolver'), form = $('#gbFormResolver');
            form.action = `/gestion-bancaria/resolver/${encodeURIComponent(confirmar.dataset.confirmarPendiente)}/`;
            form.elements.identificacion.value = confirmar.dataset.identificacion || '';
            form.elements.centro.value = '';
            form.elements.tipo_resolucion.value = 'YaImputado';
            form.elements.referencia_resolucion.value = '';
            dialogo.showModal();
        }
        if (ev.target.closest('#gbCancelarModal')) $('#gbModalResolver').close();
    });
    const res = $('#gbFormResolver');
    if (res) res.addEventListener('submit', ev => {
        if (res.elements.tipo_resolucion.value === 'ReciboGenerado' && res.elements.referencia_resolucion.value.trim().length < 3) {
            ev.preventDefault(); alert('Indicá la referencia del recibo realizado.');
        }
    });
})();
