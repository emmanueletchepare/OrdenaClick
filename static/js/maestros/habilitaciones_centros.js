/* Habilitaciones en el formulario SUPERIOR de Centros; tarjetas sólo listan.
   No altera las acciones existentes Modificar / Eliminar ni permisos HTTP. */
(() => {
    'use strict';
    const csrf = () => typeof obtenerCookie === 'function' ? obtenerCookie('csrftoken') : '';
    function seleccionarCentro(id) {
        const root = document.querySelector('[data-oc-centros-ui]');
        if (!root) return;
        const panel = root.querySelector('.oc-centros-documentacion');
        if (!panel) return;
        let elegido = null;
        root.querySelectorAll('[data-oc-habilitaciones-centro]').forEach(nodo => {
            const coincide = id && nodo.dataset.ocHabilitacionesCentro === String(id);
            nodo.hidden = !coincide;
            if (coincide) elegido = nodo;
        });
        const nombre = panel.querySelector('[data-oc-doc-centro-nombre]');
        if (nombre) nombre.textContent = elegido?.dataset.ocCentroNombre || 'Elegí un Centro';
        const ayuda = panel.querySelector('[data-oc-doc-ayuda]');
        if (ayuda) ayuda.hidden = Boolean(elegido);
        if (elegido) panel.open = true;
        if (!id) panel.open = false;
    }
    document.addEventListener('click', async ev => {
        const editar = ev.target.closest('button[data-oc-centro-editar-documentacion]');
        if (editar) {
            // El onclick original ya cargó Nombre/Tipo/Dirección en el formulario.
            seleccionarCentro(editar.dataset.ocCentroEditarDocumentacion);
            return;
        }
        if (ev.target.closest('#btnCancelarCentroOperativo')) {
            seleccionarCentro(null);
            return;
        }
        const boton = ev.target.closest('button[data-oc-habilitacion-archivar]');
        if (!boton) return;
        const contenedor = boton.closest('[data-oc-habilitaciones-centro]');
        const empresa = document.getElementById('empresaActiva')?.value;
        if (!empresa || !contenedor || !window.confirm('¿Archivar esta habilitación? Se conserva el documento y el historial.')) return;
        const centroId = contenedor.dataset.ocHabilitacionesCentro;
        boton.disabled = true;
        const datos = new FormData();
        datos.append('empresa', empresa);
        datos.append('centro', centroId);
        datos.append('habilitacion', boton.dataset.ocHabilitacionArchivar);
        try {
            const r = await fetch('/centros/habilitaciones/archivar/', {
                method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':csrf()},body:datos
            });
            const d = await r.json();
            if (!r.ok || d.ok !== true) throw Error(d.mensaje || 'No se pudo archivar.');
            await mostrarABMCentrosOperativos(origenABM);
            seleccionarCentro(centroId);
        } catch (e) { window.alert(e.message); }
        finally { if (boton.isConnected) boton.disabled = false; }
    });
    document.addEventListener('change', ev => {
        const archivo = ev.target.closest('.oc-habilitacion-adjunto input[type="file"]');
        if (!archivo) return;
        const texto = archivo.closest('.oc-habilitacion-adjunto')?.querySelector('[data-oc-archivo-nombre]');
        if (texto) texto.textContent = archivo.files?.[0]?.name || '📄 Adjuntar archivo';
    });
    document.addEventListener('submit', async ev => {
        const form = ev.target.closest('form[data-oc-habilitacion-registrar]');
        if (!form) return;
        ev.preventDefault();
        const empresa = document.getElementById('empresaActiva')?.value;
        if (!empresa) return;
        const estado = form.querySelector('.oc-habilitacion-estado');
        const boton = form.querySelector('button[type="submit"]');
        if (!boton || boton.disabled) return;
        const centroId = form.dataset.ocHabilitacionRegistrar;
        boton.disabled = true;
        if (estado) estado.textContent = 'Guardando…';
        const datos = new FormData(form);
        datos.append('empresa', empresa);
        datos.append('centro', centroId);
        try {
            const r = await fetch('/centros/habilitaciones/agregar/', {
                method:'POST',credentials:'same-origin',headers:{'X-CSRFToken':csrf()},body:datos
            });
            const d = await r.json();
            if (!r.ok || d.ok !== true) throw Error(d.mensaje || 'No se pudo registrar la habilitación.');
            await mostrarABMCentrosOperativos(origenABM);
            seleccionarCentro(centroId);
        } catch (e) {
            if (estado?.isConnected) estado.textContent = e.message;
        } finally { if (boton.isConnected) boton.disabled = false; }
    });
})();
