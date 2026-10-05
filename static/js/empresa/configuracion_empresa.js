(function(){
    "use strict";

    function tituloPanel(){
        return document.getElementById("titulo-panel");
    }

    function ejercicioPanel(){
        return document.getElementById("ejercicio-panel");
    }

    function restaurarCabeceraEmpresa(){
        const titulo = tituloPanel();
        const ejercicio = ejercicioPanel();

        if(titulo){
            const nombreEmpresa = titulo.dataset.tituloEmpresa;
            if(nombreEmpresa){
                titulo.textContent = nombreEmpresa;
            }
        }

        if(ejercicio){
            ejercicio.style.display = "";
        }
    }

    function prepararCabeceraDesignarPerfiles(){
        const titulo = tituloPanel();
        const ejercicio = ejercicioPanel();

        if(titulo){
            titulo.innerHTML = 'Designar <span>perfiles</span>';
        }

        if(ejercicio){
            ejercicio.style.display = "none";
        }
    }

    // mostrarSubmenu() vive todavía en panel_admin.html. Se expone sólo
    // este restaurador para que todo cambio de módulo pueda limpiar cabecera.
    window.restaurarCabeceraEmpresa = restaurarCabeceraEmpresa;

    function volverAConfiguracion(){
        const bloqueAlta = document.getElementById("bloque-alta-empresa");
        if(bloqueAlta){
            bloqueAlta.style.display = "none";
        }

        restaurarCabeceraEmpresa();

        if(typeof window.mostrarSubmenu === "function"){
            window.mostrarSubmenu("configuracion");
        }
    }

    function sincronizarCentro(contenedor){
        const rol = contenedor.querySelector("[data-rol-relacion]");
        const campo = contenedor.querySelector("[data-campo-centro-relacion]");
        const centro = contenedor.querySelector("[data-centro-relacion]");

        if(!rol || !campo || !centro){
            return;
        }

        const requerido = rol.value === "admin_centro";
        campo.classList.toggle("is-hidden", !requerido);
        centro.required = requerido;

        if(!requerido){
            centro.value = "";
        }
    }

    function inicializarFragmento(contenedor){
        const rol = contenedor.querySelector("[data-rol-relacion]");
        if(rol){
            rol.addEventListener("change", function(){
                sincronizarCentro(contenedor);
            });
            sincronizarCentro(contenedor);
        }

        const form = contenedor.querySelector("[data-form-solicitud-relacion]");
        if(form){
            form.addEventListener("submit", async function(event){
                event.preventDefault();

                const boton = form.querySelector('button[type="submit"]');
                if(boton){
                    boton.disabled = true;
                }

                try{
                    const respuesta = await fetch(
                        form.action,
                        {
                            method: "POST",
                            body: new FormData(form),
                            credentials: "same-origin",
                            headers: {"X-Requested-With": "XMLHttpRequest"}
                        }
                    );

                    if(!respuesta.ok){
                        throw new Error("No se pudo enviar la solicitud.");
                    }

                    contenedor.innerHTML = await respuesta.text();
                    prepararCabeceraDesignarPerfiles();
                    inicializarFragmento(contenedor);
                }catch(error){
                    console.error(error);
                    alert("No se pudo enviar la solicitud.");
                    if(boton){
                        boton.disabled = false;
                    }
                }
            });
        }
    }

    async function cargarDesignarPerfiles(url){
        const contenido = document.getElementById("contenido-operativo");
        const bloqueAlta = document.getElementById("bloque-alta-empresa");

        if(!contenido || !url){
            return;
        }

        // Limpia submenu y contenido de cualquier pantalla anterior.
        if(typeof window.limpiarPanelOperativo === "function"){
            window.limpiarPanelOperativo();
        }else{
            const submenu = document.getElementById("submenu-dinamico");
            if(submenu){
                submenu.innerHTML = "";
            }
            contenido.innerHTML = "";
        }

        if(bloqueAlta){
            bloqueAlta.style.display = "none";
        }

        prepararCabeceraDesignarPerfiles();
        contenido.innerHTML = '<div class="empty-state">Cargando perfiles...</div>';

        try{
            const separador = url.includes("?") ? "&" : "?";
            const respuesta = await fetch(
                url + separador + "fragment=1",
                {
                    credentials: "same-origin",
                    headers: {"X-Requested-With": "XMLHttpRequest"}
                }
            );

            if(!respuesta.ok){
                throw new Error("No se pudo cargar Designar perfiles.");
            }

            contenido.innerHTML = await respuesta.text();
            inicializarFragmento(contenido);
        }catch(error){
            console.error(error);
            contenido.innerHTML = '<div class="empty-state">No se pudo cargar Designar perfiles.</div>';
        }
    }

    document.addEventListener("click", function(event){
        const volverModificar = event.target.closest("#btn-volver-configuracion-empresa");
        if(volverModificar){
            event.preventDefault();
            volverAConfiguracion();
            return;
        }

        const volverRelaciones = event.target.closest("[data-volver-configuracion]");
        if(volverRelaciones){
            event.preventDefault();
            volverAConfiguracion();
            return;
        }

        const designar = event.target.closest("#btn-designar-perfiles");
        if(designar){
            event.preventDefault();
            cargarDesignarPerfiles(designar.dataset.designarPerfilesUrl);
        }
    });
})();
