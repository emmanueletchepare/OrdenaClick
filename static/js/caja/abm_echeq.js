/* Reutiliza los ABM reales de OrdenaClick sin crear formularios paralelos.
 * El borrador temporal permanece en sessionStorage de la pestaña original.
 */
var origenABM = 'echeq';
var ultimoBancoCreado = null;
const raizABMEcheq = document.getElementById('contenido-operativo');
const empresaABMEcheq = raizABMEcheq?.dataset.empresa || '';
const usuarioABMEcheq = raizABMEcheq?.dataset.usuario || '';
const vueltaABMEcheq = raizABMEcheq?.dataset.regreso || '/gestion-bancaria/';
let formularioClienteConservado = null;
function regresarAlEcheq(tipo, nombre) {
    if (tipo === 'proveedores' && nombre) {
        try {sessionStorage.setItem('ordenaclick.echeq.salida.proveedor.'+usuarioABMEcheq+'.'+empresaABMEcheq,String(nombre));}
        catch (_) {alert('No se pudo guardar el proveedor nuevo.'); return;}
    }
    if (tipo && nombre) {
        try {
            sessionStorage.setItem(`ordenaclick.echeq.abm.regreso.${usuarioABMEcheq}.${empresaABMEcheq}`,
                JSON.stringify({empresa:empresaABMEcheq,tipo,nombre}));
        } catch (_) { alert('No se pudo conservar la selección. Volvé al formulario desde la misma pestaña.'); return; }
    }
    window.location.assign(vueltaABMEcheq);
}
async function mostrarABMBancos() {
    if (ultimoBancoCreado?.nombre) {
        regresarAlEcheq('bancos',ultimoBancoCreado.nombre);
        return;
    }
    const r = await fetch(`/listar-bancos/?empresa=${encodeURIComponent(empresaABMEcheq)}`,{credentials:'same-origin'});
    if (!r.ok) {alert('No fue posible actualizar el ABM de Bancos.');return;}
    const data=await r.json();
    raizABMEcheq.innerHTML=data.html;
    iniciarABMBancos();
}
function volverDesdeABMBancos() { regresarAlEcheq(); }
async function mostrarABMClientes() {
    // guardarCliente llama esta función exclusivamente después de guardar exitosamente.
    const nombre = document.getElementById('clienteRazonSocial')?.value.trim();
    regresarAlEcheq('clientes',nombre);
}
function volverDesdeABMClientes() { regresarAlEcheq(); }
async function mostrarABMCentrosOperativos(origen='cliente') {
    if (origen !== 'cliente') return;
    if (formularioClienteConservado && ultimoCentroOperativoCreado) {
        await volverDesdeABMCentrosOperativos();
        return;
    }
    const r=await fetch(`/listar-centros-operativos/?empresa=${encodeURIComponent(empresaABMEcheq)}`,{credentials:'same-origin'});
    if (!r.ok) {alert('No fue posible abrir el ABM de Centros Operativos.');return;}
    const data=await r.json();
    if (!formularioClienteConservado) {
        formularioClienteConservado=document.createDocumentFragment();
        while(raizABMEcheq.firstChild) formularioClienteConservado.appendChild(raizABMEcheq.firstChild);
    }
    origenABM='cliente';
    raizABMEcheq.innerHTML=data.html;
    iniciarABMCentrosOperativos();
}
async function volverDesdeABMCentrosOperativos() {
    if (!formularioClienteConservado) { regresarAlEcheq();return; }
    raizABMEcheq.replaceChildren(formularioClienteConservado);
    formularioClienteConservado=null;
    origenABM='echeq';
    if (typeof actualizarCentroOperativoDelCliente==='function') await actualizarCentroOperativoDelCliente();
}
async function mostrarABMProveedores() {
    if (ultimoProveedorCreado?.id) {
        regresarAlEcheq('proveedores', ultimoProveedorCreado.id);
        return;
    }
    const r = await fetch(`/listar-proveedores/?empresa=${encodeURIComponent(empresaABMEcheq)}`, {credentials:'same-origin'});
    if (!r.ok) {alert('No fue posible actualizar el ABM de Proveedores.'); return;}
    const data = await r.json();
    raizABMEcheq.innerHTML = data.html;
    iniciarABMProveedores();
}
function volverDesdeABMProveedores() { regresarAlEcheq(); }
if(raizABMEcheq?.dataset.tipo==='proveedores') iniciarABMProveedores();
if(raizABMEcheq?.dataset.tipo==='bancos') iniciarABMBancos();
if(raizABMEcheq?.dataset.tipo==='clientes') iniciarABMClientes();
