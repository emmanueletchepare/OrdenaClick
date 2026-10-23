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
    const actualizar = () => { const marcados = hijos.filter(x=>x.checked).length; g.checked=hijos.length>0 && marcados===hijos.length;g.indeterminate=marcados>0&&marcados<hijos.length; };
    g.addEventListener('change', () => { hijos.forEach(x => {x.checked=g.checked;});actualizar(); });
    hijos.forEach(x=>x.addEventListener('change',actualizar));actualizar();
    // La casilla del título no debe cerrar el despliegue accidentalmente.
    g.addEventListener('click',e=>e.stopPropagation());
  });
})();

// Nómina: seleccionar centros es libre; marcar uno habilita el permiso.
// No concede autorizaciones sin guardar: Django valida rol, empresa y Centros.
(() => {
  const raiz = document.querySelector('.oc-acceso-form');
  if (!raiz) return;
  const permiso = raiz.querySelector('input[value="nomina.total"]');
  const centros = [...raiz.querySelectorAll('input[name="nomina_centro"]')];
  if (!permiso || !centros.length) return;

  // Nunca deshabilitar el alcance por tener el permiso inicialmente desmarcado.
  centros.forEach(centro => { centro.disabled = false; });
  const algunoMarcado = () => centros.some(centro => centro.checked);
  const limpiarError = () => centros[0].setCustomValidity('');

  permiso.addEventListener('change', () => {
    if (!permiso.checked) centros.forEach(centro => { centro.checked = false; });
    limpiarError();
  });
  centros.forEach(centro => centro.addEventListener('change', () => {
    limpiarError();
    const deseado = algunoMarcado();
    if (permiso.checked !== deseado) {
      permiso.checked = deseado;
      permiso.dispatchEvent(new Event('change', {bubbles: true}));
    }
  }));

  // El selector global de Herramientas también puede quitar Nómina.
  // En ese caso los Centros deben dejar de estar seleccionados.
  raiz.addEventListener('change', event => {
    if (event.target.matches?.('[data-oc-grupo]') && !permiso.checked) {
      centros.forEach(centro => { centro.checked = false; });
      limpiarError();
    }
  });

  raiz.addEventListener('submit', event => {
    if (permiso.checked && !algunoMarcado()) {
      event.preventDefault();
      centros[0].setCustomValidity('Seleccioná al menos un Centro para Nómina.');
      centros[0].reportValidity();
    }
  });
})();
