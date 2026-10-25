/* Gestor unificado: el selector accesible y las casillas usan los servicios B2. */
(() => {
  'use strict';
  if (window.parent !== window && window.frameElement?.id === 'ocGestionAccesosFrame') {
    document.documentElement.classList.add('oc-accesos-en-panel');
  }
  const select = document.querySelector('[data-oc-seleccionar-usuario]');
  if (!select || !select.options.length) return;
  const contenedor = select.parentElement;
  const combobox = document.createElement('div');
  combobox.className = 'oc-usuario-combobox';
  const entrada = document.createElement('input');
  entrada.type = 'search';
  entrada.className = 'oc-usuario-buscador';
  entrada.setAttribute('role', 'combobox');
  entrada.setAttribute('aria-label', 'Buscar y seleccionar usuario');
  entrada.setAttribute('aria-expanded', 'false');
  entrada.setAttribute('aria-autocomplete', 'list');
  entrada.autocomplete = 'off';
  entrada.placeholder = 'Buscar usuario…';
  const lista = document.createElement('div');
  lista.id = 'oc-usuario-opciones';
  lista.className = 'oc-usuario-opciones';
  lista.setAttribute('role', 'listbox');
  lista.hidden = true;
  entrada.setAttribute('aria-controls', lista.id);
  const items = [...select.options].map(o => ({valor:o.value, nombre:o.textContent.trim()}));
  entrada.value = select.selectedOptions[0]?.textContent.trim() || '';
  combobox.append(entrada, lista);
  contenedor.appendChild(combobox);
  select.hidden = true; // Mejora progresiva; el select queda operativo sin JS.
  let activo = -1;
  let visibles = [];

  function cerrar() {
    lista.hidden = true;
    entrada.setAttribute('aria-expanded', 'false');
    entrada.removeAttribute('aria-activedescendant');
    activo = -1;
  }
  function seleccionar(valor) {
    const item = items.find(x => x.valor === valor);
    if (!item) return;
    select.value = valor;
    entrada.value = item.nombre;
    cerrar();
    select.form.requestSubmit();
  }
  function destacar() {
    [...lista.children].forEach((n,i) => {
      n.classList.toggle('activo',i===activo);
      n.setAttribute('aria-selected',String(i===activo));
    });
    if (activo >= 0) {
      const nodo = lista.children[activo];
      entrada.setAttribute('aria-activedescendant', nodo.id);
      nodo.scrollIntoView({block:'nearest'});
    } else entrada.removeAttribute('aria-activedescendant');
  }
  function abrir(filtro='') {
    const busqueda = filtro.trim().toLocaleLowerCase('es-AR');
    visibles = items.filter(x=>x.nombre.toLocaleLowerCase('es-AR').includes(busqueda));
    lista.replaceChildren();
    activo = -1;
    if (!visibles.length) {
      const vacio = document.createElement('p');
      vacio.textContent = 'No hay coincidencias';
      vacio.className = 'oc-usuario-vacio';
      lista.append(vacio);
    } else {
      visibles.forEach((item,i)=>{
        const opcion = document.createElement('button');
        opcion.type = 'button';
        opcion.id = 'oc-usuario-item-' + i;
        opcion.className = 'oc-usuario-opcion';
        opcion.textContent = item.nombre;
        opcion.setAttribute('role','option');
        opcion.setAttribute('aria-selected','false');
        opcion.addEventListener('mousedown',e=>e.preventDefault());
        opcion.addEventListener('click',()=>seleccionar(item.valor));
        lista.append(opcion);
      });
    }
    lista.hidden = false;
    entrada.setAttribute('aria-expanded','true');
  }
  entrada.addEventListener('focus',()=>abrir(''));
  entrada.addEventListener('input',()=>abrir(entrada.value));
  entrada.addEventListener('keydown',e=>{
    if (e.key==='Escape') {cerrar();entrada.value=select.selectedOptions[0]?.textContent.trim()||'';return;}
    if (e.key==='ArrowDown'||e.key==='ArrowUp') {
      e.preventDefault();
      if (lista.hidden) abrir('');
      if (visibles.length) activo=(activo+(e.key==='ArrowDown'?1:-1)+visibles.length)%visibles.length;
      destacar();
    }
    if (e.key==='Enter' && !lista.hidden) {
      e.preventDefault();
      if (activo>=0 && visibles[activo]) seleccionar(visibles[activo].valor);
      else if (visibles.length===1) seleccionar(visibles[0].valor);
    }
  });
  entrada.addEventListener('blur',()=>{
    window.setTimeout(()=>{
      if (!combobox.contains(document.activeElement)) {
        cerrar();entrada.value=select.selectedOptions[0]?.textContent.trim()||'';
      }
    },100);
  });
  document.addEventListener('pointerdown',e=>{if(!combobox.contains(e.target)) cerrar();});
})();

(() => {
  'use strict';
  const raiz = document.querySelector('.oc-acceso-form');
  if (!raiz) return;
  raiz.querySelectorAll('[data-oc-grupo]').forEach(g => {
    const hijos = [...raiz.querySelectorAll('[data-oc-hijo="'+g.dataset.ocGrupo+'"]')].filter(x => !x.disabled);
    g.disabled = !hijos.length;
    const actualizar = () => {
      const marcados = hijos.filter(x=>x.checked).length;
      g.checked=hijos.length>0 && marcados===hijos.length;
      g.indeterminate=marcados>0&&marcados<hijos.length;
    };
    g.addEventListener('change', () => {hijos.forEach(x=>{x.checked=g.checked;});actualizar();});
    hijos.forEach(x=>x.addEventListener('change',actualizar));
    actualizar();
    g.addEventListener('click',e=>e.stopPropagation());
  });
  const permisoNomina = raiz.querySelector('input[name="capacidad"][value="nomina.total"]');
  const centros = [...raiz.querySelectorAll('input[name="nomina_centro"]')];
  if (permisoNomina && centros.length) {
    centros.forEach(c=>c.disabled=false);
    const alguna = () => centros.some(c=>c.checked);
    permisoNomina.addEventListener('change',()=>{
      if (!permisoNomina.checked) centros.forEach(c=>c.checked=false);
      centros[0].setCustomValidity('');
    });
    centros.forEach(c=>c.addEventListener('change',()=>{
      centros[0].setCustomValidity('');
      const nuevo=alguna();
      if(permisoNomina.checked!==nuevo) {
        permisoNomina.checked=nuevo;
        permisoNomina.dispatchEvent(new Event('change',{bubbles:true}));
      }
    }));
  }
  const alertaError = raiz.querySelector('.oc-alerta-error');
  function mostrarError(mensaje, entrada) {
    alertaError.textContent=mensaje;
    alertaError.hidden=false;
    entrada?.focus();
  }
  function marcado(codigo) {
    if (raiz.dataset.ocPermisosInherentes==='1') return true;
    return !!raiz.querySelector('input[name="capacidad"][value="'+codigo+'"]:checked');
  }
  function permitido(codigo) {
    if (raiz.dataset.ocPermisosInherentes==='1') return true;
    const alertas=marcado('alertas.ver');
    if (!alertas) return false;
    const propios=marcado('registros.ver')&&marcado('vencimientos.ver');
    if (codigo==='FIN-01') return marcado('vencimientos.ver');
    if (codigo==='FIN-02') return marcado('caja.total')||propios;
    if (codigo==='FIN-03') return marcado('pendientes.ver')||propios;
    if (codigo==='NOM-01') return marcado('nomina.total');
    return false;
  }
  raiz.addEventListener('change',()=>{alertaError.hidden=true;});
  raiz.addEventListener('submit',event=>{
    if(permisoNomina && centros.length && permisoNomina.checked && !centros.some(c=>c.checked)) {
      event.preventDefault();
      centros[0].setCustomValidity('Seleccioná al menos un Centro para Nómina.');
      centros[0].reportValidity();
      return;
    }
    // Comprobación UI orientativa. El backend vuelve a validar permisos y
    // alcance real por fuente; no se infieren autorizaciones de estas casillas.
    for(const a of raiz.querySelectorAll('input[name="alerta"]:checked')) {
      if(!permitido(a.value)) {
        event.preventDefault();
        mostrarError('Para asignar '+a.value+' habilitá Consultar alertas y el acceso a su fuente.',a);
        return;
      }
    }
  });
})();
