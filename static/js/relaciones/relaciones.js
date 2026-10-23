(function(){
    const role = document.getElementById('rol-relacion');
    const centerField = document.getElementById('campo-centro-relacion');
    const center = document.getElementById('centro-relacion');

    function syncCenter(){
        if(!role || !centerField || !center){return;}
        const required = role.value === 'admin_centro';
        centerField.classList.toggle('hidden', !required);
        center.required = required;
        if(!required){center.value = '';}
    }

    if(role){
        role.addEventListener('change', syncCenter);
        syncCenter();
    }

    // Confirmación en la vista independiente; la autorización la decide el servidor.
    document.querySelectorAll('[data-oc-gestionar-asignacion]').forEach(form => {
        form.addEventListener('submit', event => {
            if(form.querySelector('[name="accion"]')?.value.startsWith('revocar') &&
               !window.confirm('¿Revocar esta relación y sus accesos?')){
                event.preventDefault();
            }
        });
    });
})();
