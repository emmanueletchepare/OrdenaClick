/* Nómina: navegación contextual, CUIL con máscara y carga documental reutilizable. */
(() => {
  'use strict';
  const raiz = document.getElementById('nmRaiz');
  if (!raiz) return;
  const empresa = raiz.dataset.empresa;
  const clave = 'ordenaclick.nomina.posicion.' + empresa;
  const marco = window.frameElement;
  const panel = marco?.closest('.main');
  const parametros = new URLSearchParams(location.search);
  const idFicha = parametros.get('empleado') || (parametros.has('nuevo') ? 'nuevo' : 'listado');
  const guardar = () => {
    try { sessionStorage.setItem(clave, JSON.stringify({id: idFicha, scrollPanel: panel ? panel.scrollTop : 0, scrollFrame: window.scrollY})); }
    catch (_) { /* la navegación no depende del almacenamiento */ }
  };
  document.addEventListener('click', e => { if (e.target.closest('a,button[type="submit"]')) guardar(); }, true);
  document.addEventListener('submit', guardar, true);
  function restaurar() {
    try {
      const v = JSON.parse(sessionStorage.getItem(clave) || 'null');
      if (!v || v.id !== idFicha) return;
      if (panel) panel.scrollTop = v.scrollPanel;
      window.scrollTo(0, v.scrollFrame || 0);
    } catch (_) { /* sin sesión */ }
  }
  // El panel padre es quien desplaza la ficha integrada. Medir ambos nodos
  // evita que un cambio de altura deje un segundo scroll dentro del iframe.
  let ultimoAltoEnviado = 0;
  function avisarAlto() {
    if (!marco || window.parent === window) return;
    // Medir el contenido, no la altura del viewport del iframe: incluir
    // este último produciría un crecimiento repetido del propio iframe.
    const contenido = Math.max(raiz.offsetTop + raiz.scrollHeight,
      raiz.getBoundingClientRect().bottom + window.scrollY);
    const alto = Math.max(620, Math.ceil(contenido) + 12);
    if (alto === ultimoAltoEnviado) return;
    ultimoAltoEnviado = alto;
    parent.postMessage({tipo: 'oc-nomina-alto', alto}, location.origin);
  }
  window.addEventListener('load', () => {
    avisarAlto();
    requestAnimationFrame(() => { avisarAlto(); restaurar(); });
  });
  if (typeof ResizeObserver !== 'undefined') {
    const observar = new ResizeObserver(avisarAlto);
    observar.observe(document.body);
    observar.observe(raiz);
  }
  document.addEventListener('change', avisarAlto);

  // Misma regla de CUIT: 11 dígitos almacenados, 13 caracteres con guiones en pantalla.
  function mascaraCuil(valor) {
    const digitos = String(valor || '').replace(/\D/g, '').slice(0, 11);
    if (digitos.length <= 2) return digitos;
    if (digitos.length <= 10) return digitos.slice(0, 2) + '-' + digitos.slice(2);
    return digitos.slice(0, 2) + '-' + digitos.slice(2, 10) + '-' + digitos.slice(10);
  }
  const cuil = document.querySelector('#nmFormulario [name="cuil"]');
  if (cuil) {
    cuil.maxLength = 13;
    cuil.inputMode = 'numeric';
    cuil.placeholder = '20-32390769-3';
    cuil.value = mascaraCuil(cuil.value);
    cuil.addEventListener('input', () => {
      const posicion = cuil.selectionStart || 0;
      const anteriores = (cuil.value.slice(0, posicion).match(/\d/g) || []).length;
      const convertido = mascaraCuil(cuil.value);
      cuil.value = convertido;
      let cursor = 0, contados = 0;
      while (cursor < convertido.length && contados < anteriores) {
        if (/\d/.test(convertido[cursor])) contados += 1;
        cursor += 1;
      }
      if (anteriores > 0 && convertido[cursor] === '-') cursor += 1;
      cuil.setSelectionRange(cursor, cursor);
    });
  }

  // La elección del archivo se muestra como en la documentación societaria.
  document.querySelectorAll('.nm-file-btn input[type="file"]').forEach(input => {
    const texto = input.closest('.nm-file-btn')?.querySelector('.nm-file-text');
    if (!texto) return;
    input.addEventListener('change', () => {
      texto.textContent = input.files?.[0]?.name || '📄 Adjuntar archivo';
      avisarAlto();
    });
  });

  // Los [+] abren el ABM original en el mismo panel, nunca una pestaña nueva.
  document.addEventListener('click', e => {
    const boton = e.target.closest('[data-nomina-abm]');
    if (!boton) return;
    e.preventDefault();
    const abrir = window.parent?.OrdenaClickNominaAbrirABM;
    if (window.parent === window || typeof abrir !== 'function') {
      alert('Abrí Nómina desde Herramientas para utilizar este ABM.');
      return;
    }
    guardar();
    abrir(boton.dataset.nominaAbm);
  });

  window.OrdenaClickNominaActualizarSelect = function(campo, opciones, nuevoId) {
    const select = document.querySelector('#nmFormulario [name="' + campo + '"]');
    if (!select || !Array.isArray(opciones)) return;
    const anterior = select.value;
    const primera = select.querySelector('option[value=""]')?.textContent || 'Seleccionar';
    select.replaceChildren(new Option(primera, ''));
    for (const o of opciones) select.add(new Option(o.nombre, String(o.id)));
    const valores = new Set([...select.options].map(o => o.value));
    select.value = nuevoId && valores.has(nuevoId) ? nuevoId : (valores.has(anterior) ? anterior : '');
    select.dispatchEvent(new Event('change', {bubbles: true}));
    avisarAlto();
  };
})();
