(function () {
    'use strict';
    const lotes = {bancos: [], echeqs: []};
    const edicion = {bancos: null, echeqs: null};
    let guardando = false;
    const $ = (selector, base=document) => base.querySelector(selector);
    const campos = {
        bancos: ['tipo', 'fecha', 'identificacion', 'importe'],
        echeqs: ['titular', 'numero', 'banco', 'banco_id', 'importe', 'acreditacion', 'condicion']
    };
    function formatoImporte(valor) {
        const texto = String(valor).trim();
        const normal = texto.includes(',') ? texto.replace(/\./g, '').replace(',', '.') :
            (/^\d{1,3}(?:\.\d{3})+$/.test(texto) ? texto.replace(/\./g, '') : texto);
        const n = Number(normal);
        return Number.isFinite(n) && n >= 0 ? n.toLocaleString('es-AR', {minimumFractionDigits:2, maximumFractionDigits:2}) : String(valor);
    }
    // Un cheque siempre se muestra como 8 dígitos, igual que Carga Simple.
    function normalizarNumeroEcheq(input) {
        const numero = input.value.trim();
        input.setCustomValidity('');
        if (!numero) return;
        if (!/^\d{1,8}$/.test(numero)) {
            input.setCustomValidity('El número del e-Cheq debe tener sólo dígitos, hasta 8.');
            return;
        }
        input.value = numero.padStart(8, '0');
    }
    function normalizarImporteInput(input) {
        const texto = input.value.trim();
        if (!texto) return;
        const normal = texto.includes(',') ? texto.replace(/\./g, '').replace(',', '.') :
            (/^\d{1,3}(?:\.\d{3})+$/.test(texto) ? texto.replace(/\./g, '') : texto);
        if (!/^\d+(?:\.\d{1,2})?$/.test(normal)) return;
        input.value = Number(normal).toLocaleString('es-AR', {minimumFractionDigits:2, maximumFractionDigits:2});
    }
    // El borrador sólo vive en esta pestaña; no es un registro financiero.
    const raiz = $('#gbRaiz');
    const empresa = raiz ? raiz.dataset.empresa : '';
    const usuario = raiz ? raiz.dataset.usuario : '';
    const borradorClave = `ordenaclick.echeq.borrador.${usuario}.${empresa}`;
    const regresoClave = `ordenaclick.echeq.abm.regreso.${usuario}.${empresa}`;
    const destinoClave = `ordenaclick.echeq.abm.destino.${usuario}.${empresa}`;
    function almacenarBorrador() {
        try {
            const valores = {};
            for (const clase of ['bancos', 'echeqs']) {
                const form = $('#gbCarga' + (clase === 'bancos' ? 'Bancos' : 'Echeqs'));
                valores[clase] = {};
                for (const elemento of Array.from(form.elements)) {
                    if (elemento.name && elemento.name !== 'csrfmiddlewaretoken') valores[clase][elemento.name] = elemento.value;
                }
            }
            sessionStorage.setItem(borradorClave, JSON.stringify({empresa, lotes, edicion, valores, pestaña: document.querySelector('.gb-pestana.activa')?.dataset.tipoCarga || 'echeqs'}));
            return true;
        } catch (_) { return false; }
    }
    function recuperarBorrador() {
        try {
            const guardado = sessionStorage.getItem(borradorClave);
            if (!guardado) return;
            const draft = JSON.parse(guardado);
            if (draft.empresa !== empresa || !draft.lotes || !draft.valores) return;
            for (const clase of ['bancos','echeqs']) {
                if (!Array.isArray(draft.lotes[clase]) || draft.lotes[clase].length > 80) return;
            }
            for (const clase of ['bancos','echeqs']) {
                lotes[clase] = draft.lotes[clase];
                edicion[clase] = Number.isInteger(draft.edicion[clase]) ? draft.edicion[clase] : null;
                const form = $('#gbCarga' + (clase === 'bancos' ? 'Bancos' : 'Echeqs'));
                for (const [nombre, valor] of Object.entries(draft.valores[clase])) {
                    if (form.elements.namedItem(nombre) && typeof valor === 'string' && nombre !== 'csrfmiddlewaretoken') form.elements[nombre].value = valor;
                }
                render(clase);
            }
            const pestaña = draft.pestaña === 'bancos' ? 'bancos' : 'echeqs';
            document.querySelectorAll('[data-pantalla-carga]').forEach(el => {el.hidden = el.dataset.pantallaCarga !== pestaña;});
            document.querySelectorAll('[data-tipo-carga]').forEach(el => {el.classList.toggle('activa', el.dataset.tipoCarga === pestaña);});
            sessionStorage.removeItem(borradorClave);
            const regreso = JSON.parse(sessionStorage.getItem(regresoClave) || 'null');
            sessionStorage.removeItem(regresoClave);
            if (regreso && regreso.empresa === empresa && regreso.nombre) {
                const destino = sessionStorage.getItem(destinoClave) || 'echeqs';
                sessionStorage.removeItem(destinoClave);
                const formulario = $('#gbCarga' + (destino === 'bancos' ? 'Bancos' : 'Echeqs'));
                const input = regreso.tipo === 'clientes' ? formulario.elements[destino === 'bancos' ? 'identificacion' : 'titular'] : $('#gbCargaEcheqs').elements.banco;
                input.value = regreso.nombre;
                if (regreso.tipo === 'bancos') actualizarBancoSeleccionado($('#gbCargaEcheqs'));
            }
        } catch (_) { /* Sin cambiar datos financieros si falla storage. */ }
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
        if (clase === 'echeqs') {
            actualizarBancoSeleccionado(form);
            normalizarNumeroEcheq(form.elements.numero);
        }
        normalizarImporteInput(form.elements.importe);
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
    function normalizarNombreBanco(valor) {
        return String(valor || '').trim().toLocaleUpperCase('es-AR');
    }
    function actualizarBancoSeleccionado(form) {
        const nombre = form.elements.banco.value;
        const id = form.elements.banco_id;
        const coincidente = Array.from($('#gbBancosEmisores').options).find(
            option => normalizarNombreBanco(option.value) === normalizarNombreBanco(nombre)
        );
        id.value = coincidente ? coincidente.dataset.id : '';
        return !!coincidente;
    }
    function agregar(clase, form) {
        if (clase === 'echeqs' && !actualizarBancoSeleccionado(form)) {
            form.elements.banco.setCustomValidity('Elegí un banco registrado o crealo con [+].');
            form.reportValidity();
            return;
        }
        if (clase === 'echeqs') normalizarNumeroEcheq(form.elements.numero);
        normalizarImporteInput(form.elements.importe);
        if (!form.reportValidity()) return;
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
        const cuenta = clase === 'bancos' ? form.elements.cuenta.value : null;
        const mensaje = $(`[data-mensaje-lote="${clase}"]`);
        if (clase === 'bancos' && !cuenta) {mensaje.textContent = 'Seleccioná la cuenta bancaria antes de guardar.'; return;}
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
        if (form) form.addEventListener('submit', ev => {
            ev.preventDefault();
            if (clase === 'echeqs') normalizarNumeroEcheq(form.elements.numero);
            normalizarImporteInput(form.elements.importe);
            if (form.reportValidity()) agregar(clase, form);
        });
    }
    const formEcheqs = $('#gbCargaEcheqs');
    if (formEcheqs) {
        const banco = formEcheqs.elements.banco;
        banco.addEventListener('input', () => {
            banco.setCustomValidity('');
            actualizarBancoSeleccionado(formEcheqs);
        });
        banco.addEventListener('change', () => actualizarBancoSeleccionado(formEcheqs));
        formEcheqs.elements.numero.addEventListener('blur', () => normalizarNumeroEcheq(formEcheqs.elements.numero));
    }
    for (const formulario of ['gbCargaBancos','gbCargaEcheqs']) {
        const input = $('#' + formulario).elements.importe;
        input.addEventListener('blur', () => normalizarImporteInput(input));
    }
    document.querySelectorAll('[data-abrir-abm]').forEach(enlace => {
        enlace.addEventListener('click', evento => {
            if (guardando || !almacenarBorrador()) {
                evento.preventDefault();
                alert('No se pudo preservar la carga. No saldremos para evitar perder datos.');
            } else {
                try {sessionStorage.setItem(destinoClave, enlace.dataset.destinoAbm || 'echeqs');}
                catch (_) {evento.preventDefault(); alert('No se pudo preservar el retorno al formulario.');}
            }
        });
    });
    recuperarBorrador();

    document.addEventListener('change', ev => {
        if (ev.target.matches('.gb-filtro select')) ev.target.form.submit();
    });
    const buscar = $('#gbBuscarPendientes');
    if (buscar) {
        let debounce;
        buscar.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(() => {
                // No recarga el borrador del e-Cheq mientras aún se está preparando.
                const q = new URLSearchParams(new FormData(buscar.form));
                q.delete('pagina');
                fetch(`${window.location.pathname}?${q.toString()}`, {credentials:'same-origin', cache:'no-store'})
                    .then(r => {if(!r.ok) throw new Error();return r.text();})
                    .then(texto => {
                        if (document.activeElement !== buscar) return;
                        const dom = new DOMParser().parseFromString(texto, 'text/html');
                        const tabla = $('#bandejaPendientes .gb-tabla tbody');
                        const nueva = $('#bandejaPendientes .gb-tabla tbody', dom);
                        const pag = $('#bandejaPendientes .gb-paginacion');
                        const nuevaPag = $('#bandejaPendientes .gb-paginacion', dom);
                        if (tabla && nueva && pag && nuevaPag) {
                            tabla.replaceChildren(...Array.from(nueva.children));
                            pag.replaceChildren(...Array.from(nuevaPag.children));
                            history.replaceState(null, '', `${window.location.pathname}?${q.toString()}`);
                        }
                    }).catch(() => { /* Fallo de consulta no altera la carga. */ });
            }, 280);
        });
    }
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
        const rev = ev.target.closest('[data-revisar-pendiente]');
        if (rev) {
            const dialogo = $('#gbModalRevision'), form = $('#gbFormRevision');
            const pendiente = rev.dataset.estado === 'Pendiente';
            form.action = `/gestion-bancaria/revisar/${encodeURIComponent(rev.dataset.revisarPendiente)}/`;
            form.elements.motivo.value = '';
            form.elements.fecha.value = rev.dataset.fecha;
            form.elements.identificacion.value = rev.dataset.identificacion;
            form.elements.importe.value = rev.dataset.importe;
            form.elements.numero.value = rev.dataset.numero;
            form.elements.titular.value = rev.dataset.titular;
            form.elements.banco.value = rev.dataset.banco;
            form.elements.clave.value = nuevoId();
            $('#gbRevisionError').textContent = '';
            normalizarImporteInput(form.elements.importe);
            $('#gbRevisionCampos').hidden = !pendiente;
            $('#gbRevisionEcheq').hidden = rev.dataset.tipo !== 'ECheq';
            $('#gbRevisionTitulo').textContent = pendiente ? 'Editar pendiente con auditoría' : 'Informar error para auditoría';
            $('#gbRevisionAyuda').textContent = pendiente ? 'El cambio conservará los datos anteriores y su motivo.' : 'El resuelto no se alterará: se registrará una incidencia para que administración pueda revisarla.';
            $('#gbRevisionEnviar').textContent = pendiente ? 'Guardar corrección' : 'Abrir auditoría';
            form.dataset.tipo = rev.dataset.tipo;
            dialogo.showModal();
        }
        if (ev.target.closest('#gbCancelarRevision')) $('#gbModalRevision').close();
    });
    const revisarForm = $('#gbFormRevision');
    if (revisarForm) {
        revisarForm.elements.numero.addEventListener('blur', () => normalizarNumeroEcheq(revisarForm.elements.numero));
        revisarForm.elements.importe.addEventListener('blur', () => normalizarImporteInput(revisarForm.elements.importe));
        revisarForm.addEventListener('submit', async ev => {
            ev.preventDefault();
            const mensaje = $('#gbRevisionError');
            if (!$('#gbRevisionCampos').hidden && revisarForm.dataset.tipo === 'ECheq') normalizarNumeroEcheq(revisarForm.elements.numero);
            normalizarImporteInput(revisarForm.elements.importe);
            if (!revisarForm.reportValidity()) return;
            const boton = $('#gbRevisionEnviar');
            boton.disabled = true;
            mensaje.textContent = 'Registrando revisión...';
            try {
                const resp = await fetch(revisarForm.action, {
                    method:'POST', credentials:'same-origin',
                    headers:{'X-Requested-With':'XMLHttpRequest'},
                    body:new FormData(revisarForm),
                });
                const datos = await resp.json();
                if (!resp.ok || !datos.ok) throw new Error(datos.mensaje || 'No se pudo registrar la revisión.');
                window.location.assign(datos.destino);
            } catch (error) {
                mensaje.textContent = error.message;
                boton.disabled = false;
            }
        });
    }
    const res = $('#gbFormResolver');
    if (res) res.addEventListener('submit', ev => {
        if (res.elements.tipo_resolucion.value === 'ReciboGenerado' && res.elements.referencia_resolucion.value.trim().length < 3) {
            ev.preventDefault(); alert('Indicá la referencia del recibo realizado.');
        }
    });
})();
