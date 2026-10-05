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
})();
