(() => {
  'use strict';
  if (window.parent !== window && window.frameElement?.id === 'ocGestionAccesosFrame') {
    document.documentElement.classList.add('oc-accesos-en-panel');
  }
  document.querySelector('[data-oc-seleccionar-usuario]')?.addEventListener('change', e => e.target.form.requestSubmit());
  const raiz = document.querySelector('.oc-acceso-form'); if (!raiz) return;
  raiz.querySelectorAll('[data-oc-grupo]').forEach(g => {
    const hijos = [...raiz.querySelectorAll('[data-oc-hijo="'+g.dataset.ocGrupo+'"]')].filter(x => !x.disabled);
    g.disabled = !hijos.length;
    const actualizar = () => { const marcados = hijos.filter(x=>x.checked).length; g.checked=marcados===hijos.length;g.indeterminate=marcados>0&&marcados<hijos.length; };
    g.addEventListener('change', () => { hijos.forEach(x => {x.checked=g.checked;});actualizar(); });
    hijos.forEach(x=>x.addEventListener('change',actualizar));actualizar();
    // La casilla del título no debe cerrar el despliegue accidentalmente.
    g.addEventListener('click',e=>e.stopPropagation());
  });
})();
