/* Navegación restringida: invoca los MISMO ABM del Administrador sin cargar su panel privado. */
(() => {
  'use strict';
  const ruta = {
    centros:'mostrarABMCentrosOperativos', recursos:'mostrarABMRecursosOperativos',
    proveedores:'mostrarABMProveedores', tipos:'mostrarABMTiposGasto',
    clientes:'mostrarABMClientes', bancos:'mostrarABMBancos',
    cuentas:'mostrarABMCuentasBancarias', tarjetas:'mostrarABMTarjetas',
    retenciones:'mostrarABMRetenciones', claves:'mostrarABMGestionClaves'
  };
  window.mostrarSubmenu = function() {
    const contenido=document.getElementById('contenido-operativo');
    if (contenido) contenido.replaceChildren();
  };
  window.mostrarABMGestionClaves = async function() {
    const empresa=document.getElementById('empresaActiva')?.value;
    const area=document.getElementById('contenido-operativo');
    if(!empresa || !area) return;
    const r=await fetch('/gestion-claves/?empresa='+encodeURIComponent(empresa),{credentials:'same-origin'});
    const d=await r.json(); if(!r.ok || !d.ok){alert(d.mensaje||'No autorizado.');return;}
    area.innerHTML=d.html;
    if(typeof iniciarABMGestionClaves==='function')iniciarABMGestionClaves();
  };
  window.volverDesdeGestionClaves = () => window.mostrarSubmenu();
  document.addEventListener('click',async e=>{
    const b=e.target.closest('[data-oc-modulo]');if(!b)return;
    const f=window[ruta[b.dataset.ocModulo]];
    if(typeof f!=='function')return;
    b.disabled=true;
    try{await f('menu');}catch(error){console.error('Módulo autorizado no disponible',error);alert('No se pudo abrir este módulo.');}
    finally{b.disabled=false;}
  });
})();
