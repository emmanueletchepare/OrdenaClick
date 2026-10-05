(function(){
    const form=document.getElementById('form-importacion');
    const input=document.getElementById('archivo-importacion');
    const trigger=document.getElementById('btn-importar-empresa');
    if(trigger&&input){trigger.addEventListener('click',function(){input.click();});}
    if(form&&input){input.addEventListener('change',function(){if(input.files&&input.files.length){form.submit();}});}
})();
