(function(){
    function syncUserRow(row){
        const active=row.querySelector('[data-active-toggle]');
        const role=row.querySelector('[data-role-select]');
        const center=row.querySelector('[data-center-select]');
        if(!role||!center){return;}
        const enabled=!active||active.checked;
        role.disabled=!enabled;
        const requiresCenter=enabled&&role.value==='admin_centro';
        center.disabled=!requiresCenter;
        const field=center.closest('.center-field');
        if(field){field.classList.toggle('hidden',!requiresCenter);}
        if(!requiresCenter){center.value='';}
    }

    function syncFileLabel(input){
        const targetId=input.dataset.fileLabel;
        if(!targetId){return;}
        const label=document.getElementById(targetId);
        if(!label){return;}
        label.textContent=input.files&&input.files.length>0
            ? '📄 '+input.files[0].name
            : '📄 Adjuntar archivo';
    }

    document.querySelectorAll('[data-user-row]').forEach(function(row){
        const active=row.querySelector('[data-active-toggle]');
        const role=row.querySelector('[data-role-select]');
        if(active){active.addEventListener('change',function(){syncUserRow(row);});}
        if(role){role.addEventListener('change',function(){syncUserRow(row);});}
        syncUserRow(row);
    });

    document.querySelectorAll('input[type="file"][data-file-label]').forEach(function(input){
        input.addEventListener('change',function(){syncFileLabel(input);});
        syncFileLabel(input);
    });
})();
