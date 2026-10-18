/* Salidas e-Cheq: selección explícita; backend es autoridad para validar disponibilidad. */
(() => {
 'use strict';
 const raiz = document.getElementById('cargaBancaria'); if (!raiz) return;
 const moneda = x => Number(x).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2});
 const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const datos = {Depositar:[],EndosarCeder:[]};
 const seleccion = {Depositar:new Set(),EndosarCeder:new Set()};
 const empresa = document.getElementById('gbRaiz')?.dataset.empresa;
 const usuario = document.getElementById('gbRaiz')?.dataset.usuario;
 const retornoClave = 'ordenaclick.echeq.salida.borrador.'+usuario+'.'+empresa;
 const abmClave = 'ordenaclick.echeq.salida.proveedor.'+usuario+'.'+empresa;
 const envio = {Depositar:null,EndosarCeder:null};
 const mensaje = tipo => document.querySelector('[data-salida-mensaje="'+tipo+'"]');
 const pesos = ids => ids.reduce((s,v)=>s+Math.round(Number(v.importe)*100),0);
 const dinero = n => '$ '+moneda(n/100);
 const vigente = v => {const d=new Date(v.acreditacion+'T12:00:00'), hoy=new Date(); hoy.setHours(12,0,0,0); return !!v.acreditacion && hoy>=d && hoy<new Date(d.getTime()+30*86400000);};
 function pintar(tipo){
  const filas=document.querySelector('[data-salida-filas="'+tipo+'"]'); if(!filas)return;
  const items=datos[tipo].filter(v=>tipo!=='Depositar'||vigente(v)).sort((a,b)=>(a.acreditacion||'9999-99-99').localeCompare(b.acreditacion||'9999-99-99')||a.id-b.id);
  filas.innerHTML=items.length?items.map(v=>'<tr class="'+(seleccion[tipo].has(v.id)?'gb-salida-elegido':'')+'"><td><label class="gb-salida-switch"><input type="checkbox" data-elegir-salida="'+tipo+'" value="'+v.id+'" '+(seleccion[tipo].has(v.id)?'checked':'')+'><span></span></label></td><td>'+esc(v.numero)+'<small>'+esc(v.titular)+'</small></td><td>'+esc(v.acreditacion)+'</td><td>'+ (v.condicion==='Orden'?'<span class="gb-condicion-orden">A la orden</span>':v.condicion==='NoOrden'?'<span class="gb-condicion-noorden">No a la orden</span>':'Condición sin clasificar')+'</td><td class="gb-numero">'+dinero(Math.round(Number(v.importe)*100))+'</td></tr>').join(''):'<tr><td colspan="5" class="gb-vacio">No hay e-Cheqs disponibles para esta operación.</td></tr>';
  const elegidos=items.filter(v=>seleccion[tipo].has(v.id));
  const tot=document.querySelector('[data-salida-totales="'+tipo+'"]');
  if(tipo==='Depositar')tot.textContent='Total depósito: '+dinero(pesos(elegidos));
  else {const end=elegidos.filter(v=>v.condicion==='Orden'), ced=elegidos.filter(v=>v.condicion!=='Orden');tot.textContent='Cheques a endosar: '+dinero(pesos(end))+' · Cheques a ceder: '+dinero(pesos(ced))+' · Total operación: '+dinero(pesos(elegidos));}
 }
 async function cargar(){
  try {const r=await fetch('/gestion-bancaria/salidas/',{credentials:'same-origin',cache:'no-store'});const d=await r.json();if(!r.ok||!d.ok)throw Error(d.mensaje||'No se pudo consultar la cartera.');
   for(const tipo of ['Depositar','EndosarCeder']){datos[tipo]=d.instrumentos;seleccion[tipo].clear();pintar(tipo);mensaje(tipo).textContent='';}
  }catch(e){for(const tipo of ['Depositar','EndosarCeder'])mensaje(tipo).textContent=e.message;}
 }
 document.addEventListener('click', async e=>{
  const tab=e.target.closest('[data-tipo-carga]');if(tab&&['endosos','salida_deposito'].includes(tab.dataset.tipoCarga))await cargar();
  const btn=e.target.closest('[data-salida-confirmar]');if(!btn)return;
  const tipo=btn.dataset.salidaConfirmar;
  const ids=[...seleccion[tipo]];
  if(!ids.length){mensaje(tipo).textContent='Seleccioná al menos un e-Cheq.';return;}
  const panel=document.querySelector('[data-salida="'+tipo+'"]');
  const payload={clave:envio[tipo]?.clave||crypto.randomUUID(),tipo,ids};
  if(tipo==='Depositar')payload.cuenta=panel.querySelector('[data-salida-cuenta]').value;
  else {const nombre=panel.querySelector('[data-salida-proveedor-buscar]').value.trim();
   const opcion=[...panel.querySelectorAll('#gbProveedoresSalida option')].find(o=>o.value===nombre);
   payload.proveedor=opcion?.dataset.id||'';panel.querySelector('[data-salida-proveedor]').value=payload.proveedor;payload.banco=panel.querySelector('[data-salida-banco]').value;payload.destino=panel.querySelector('[data-salida-destino]').value.trim();}
  if(!(tipo==='Depositar'?payload.cuenta:(payload.proveedor&&payload.banco&&payload.destino))){mensaje(tipo).textContent='Completá los datos del destino.';return;}
   if(tipo==='EndosarCeder' && payload.destino.length>80){mensaje(tipo).textContent='El destino admite hasta 80 caracteres.';return;}
  if(!window.confirm('¿Confirmar salida de '+ids.length+' e-Cheq(s)? No se podrá deshacer automáticamente.'))return;
  if(envio[tipo] && (JSON.stringify(envio[tipo].ids)!==JSON.stringify(ids) || JSON.stringify({...envio[tipo],clave:null})!==JSON.stringify({...payload,clave:null}))){mensaje(tipo).textContent='Primero comprobá la operación anterior antes de cambiar el destino o la selección.';return;}
  envio[tipo]=payload;
  btn.disabled=true; mensaje(tipo).textContent='Registrando operación...';
  try{const token=document.querySelector('#gbCargaEcheqs input[name="csrfmiddlewaretoken"]')?.value;
   const r=await fetch('/gestion-bancaria/salidas/confirmar/',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':token||''},body:JSON.stringify(payload)});
   const d=await r.json();if(!r.ok||!d.ok)throw Error(d.mensaje||'No se pudo registrar.');
   envio[tipo]=null;await cargar();mensaje(tipo).textContent='Operación #'+d.operacion+' confirmada. Los e-Cheqs salieron de cartera.';
   if(tipo==='EndosarCeder'){const dialogo=document.getElementById('gbPdfSalidaDialogo');if(dialogo){dialogo.dataset.operacion=d.operacion;dialogo.showModal();}}
  }catch(err){mensaje(tipo).textContent=err.message+' Si hubo un corte de red, comprobá el historial antes de reintentar.';}
  finally{btn.disabled=false;}
 });
 document.getElementById('gbPdfSalidaCancelar')?.addEventListener('click',()=>document.getElementById('gbPdfSalidaDialogo')?.close());
 document.getElementById('gbPdfSalidaAceptar')?.addEventListener('click',()=>{const modal=document.getElementById('gbPdfSalidaDialogo');const id=modal?.dataset.operacion;if(!/^\d+$/.test(id||''))return;window.open('/gestion-bancaria/salidas/'+id+'/pdf/','_blank','noopener');modal.close();});
 document.addEventListener('click',e=>{
   const mas=e.target.closest('a[data-abrir-abm="proveedores"]'); if(!mas)return;
   const panel=document.querySelector('[data-salida="EndosarCeder"]');
   try {sessionStorage.setItem(retornoClave, JSON.stringify({empresa, tipo:'EndosarCeder',
       proveedor:panel.querySelector('[data-salida-proveedor]').value,
       proveedorNombre:panel.querySelector('[data-salida-proveedor-buscar]').value,
       banco:panel.querySelector('[data-salida-banco]').value,
       destino:panel.querySelector('[data-salida-destino]').value,
       ids:[...seleccion.EndosarCeder], scrollY:window.scrollY,
        scrollPanel:window.frameElement?.closest('.main')?.scrollTop ?? null}));}
   catch(_){e.preventDefault();alert('No se pudo preservar la selección; no se abrió el ABM.');}
 });
 async function recuperar(){
  let estado=null;
  try{estado=JSON.parse(sessionStorage.getItem(retornoClave)||'null');}catch(_){}
  if(!estado||estado.empresa!==empresa)return;
  try{await cargar();}catch(_){};
  const panel=document.querySelector('[data-salida="EndosarCeder"]');
  panel.querySelector('[data-salida-banco]').value=estado.banco;
  panel.querySelector('[data-salida-destino]').value=estado.destino;
  const idNuevo=sessionStorage.getItem(abmClave);
  const proveedor=panel.querySelector('[data-salida-proveedor]');
  const datalist=panel.querySelector('#gbProveedoresSalida');
  if(idNuevo && ![...datalist.options].some(o=>o.dataset.id===idNuevo)){
   // El proveedor recién creado no estaba en el HTML anterior: pedir la pantalla actualizada.
   const r=await fetch(location.pathname+location.search,{credentials:'same-origin',cache:'no-store'});
   if(r.ok){const dom=new DOMParser().parseFromString(await r.text(),'text/html');
    const nuevo=dom.querySelector('#gbProveedoresSalida');if(nuevo)datalist.replaceChildren(...[...nuevo.options].map(o=>o.cloneNode(true)));}
  }
  proveedor.value=idNuevo||estado.proveedor;
  const opcionElegida=[...datalist.options].find(o=>o.dataset.id===proveedor.value);
  panel.querySelector('[data-salida-proveedor-buscar]').value=opcionElegida?.value||estado.proveedorNombre||'';
  seleccion.EndosarCeder=new Set(estado.ids.filter(id=>datos.EndosarCeder.some(v=>v.id===id)));
  pintar('EndosarCeder');
  document.querySelectorAll('[data-pantalla-carga]').forEach(el=>el.hidden=el.dataset.pantallaCarga!=='endosos');
  document.querySelectorAll('[data-tipo-carga]').forEach(el=>el.classList.toggle('activa',el.dataset.tipoCarga==='endosos'));
  sessionStorage.removeItem(abmClave);sessionStorage.removeItem(retornoClave);
   requestAnimationFrame(()=>requestAnimationFrame(()=>{
    window.scrollTo(0,estado.scrollY||0);
    const contenedor=window.frameElement?.closest('.main');
    if(contenedor && Number.isFinite(estado.scrollPanel)) contenedor.scrollTop=estado.scrollPanel;
   }));
 }
 recuperar();
 document.addEventListener('change',e=>{if(!e.target.matches('[data-elegir-salida]'))return;const tipo=e.target.dataset.elegirSalida,id=Number(e.target.value);if(e.target.checked)seleccion[tipo].add(id);else seleccion[tipo].delete(id);pintar(tipo);});
})();
