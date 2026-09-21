/**
 * Gestiona la navegación y las acciones técnicas
 * del Perfil Desarrollador.
 *
 * Las decisiones de seguridad y la modificación de secretos
 * pertenecen siempre al backend. Este archivo únicamente
 * coordina la interacción del usuario.
 */
document.addEventListener(
    "DOMContentLoaded",
    function(){

        const botones =
            document.querySelectorAll(
                "[data-developer-module]"
            );

        const contenidos =
            document.querySelectorAll(
                "[data-developer-content]"
            );

        const botonReemplazarSecretKey =
            document.querySelector(
                "[data-secret-key-replace]"
            );

        const formularioSecretKey =
            document.querySelector(
                "[data-secret-key-form]"
            );
        
        const formularioArca =
            document.querySelector(
                "[data-arca-form]"
            );

        const botonGuardarArca =
            document.querySelector(
                "[data-arca-save]"
            );

        botones.forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const modulo =
                            boton.dataset.developerModule;


                        botones.forEach(
                            function(item){

                                item.classList.remove(
                                    "activo"
                                );

                            }
                        );


                        contenidos.forEach(
                            function(contenido){

                                contenido.hidden =
                                    contenido.dataset.developerContent
                                    !== modulo;

                            }
                        );


                        boton.classList.add(
                            "activo"
                        );

                    }
                );

            }
        );


        if(
            botonReemplazarSecretKey
            && formularioSecretKey
        ){

            botonReemplazarSecretKey.addEventListener(
                "click",
                async function(){

                    const confirmado =
                        window.confirm(
                            "¿Preparar una nueva SECRET_KEY?\n\n" +
                            "La clave actual continuará en uso hasta " +
                            "reiniciar OrdenaClick.\n\n" +
                            "El cambio puede invalidar sesiones y " +
                            "otros datos firmados con la clave anterior."
                        );


                    if(!confirmado){
                        return;
                    }


                    botonReemplazarSecretKey.disabled = true;


                    try{

                        const datosFormulario =
                            new FormData(
                                formularioSecretKey
                            );


                        const respuesta =
                            await fetch(
                                formularioSecretKey.action,
                                {
                                    method: "POST",
                                    body: datosFormulario,
                                    credentials: "same-origin",
                                    headers: {
                                        "X-Requested-With":
                                            "XMLHttpRequest"
                                    }
                                }
                            );


                        let datos;

                        try{

                            datos =
                                await respuesta.json();

                        }
                        catch(error){

                            throw new Error(
                                "Respuesta inválida del servidor."
                            );

                        }


                        if(!respuesta.ok){

                            if(
                                respuesta.status === 409
                                && datos.requiere_reinicio
                            ){

                                window.alert(
                                    datos.error
                                );

                                window.location.reload();
                                return;

                            }


                            throw new Error(
                                datos.error
                                || "No se pudo preparar la nueva clave."
                            );

                        }


                        if(
                            !datos.ok
                            || !datos.requiere_reinicio
                        ){

                            throw new Error(
                                "El servidor no confirmó correctamente " +
                                "la preparación de la nueva clave."
                            );

                        }


                        window.alert(
                            datos.mensaje
                        );

                        window.location.reload();

                    }
                    catch(error){

                        window.alert(
                            error.message
                            || "No se pudo preparar la nueva SECRET_KEY."
                        );

                        botonReemplazarSecretKey.disabled = false;

                    }

                }
            );

        }

        if(
            formularioArca
            && botonGuardarArca
        ){

            botonGuardarArca.addEventListener(
                "click",
                async function(){

                    const confirmado =
                        window.confirm(
                            "¿Guardar la configuración de ARCA?\n\n" +
                            "El ambiente seleccionado será utilizado " +
                            "por las consultas de OrdenaClick."
                        );

                    if(!confirmado){
                        return;
                    }

                    botonGuardarArca.disabled = true;

                    try{

                        const datosFormulario =
                            new FormData(
                                formularioArca
                            );

                        const respuesta =
                            await fetch(
                                formularioArca.action,
                                {
                                    method: "POST",
                                    body: datosFormulario,
                                    credentials: "same-origin",
                                    headers: {
                                        "X-Requested-With":
                                            "XMLHttpRequest"
                                    }
                                }
                            );

                        let datos;

                        try{

                            datos =
                                await respuesta.json();

                        }
                        catch(error){

                            throw new Error(
                                "Respuesta inválida del servidor."
                            );

                        }

                        if(!respuesta.ok){

                            throw new Error(
                                datos.error
                                || "No se pudo guardar la configuración de ARCA."
                            );

                        }

                        if(!datos.ok){

                            throw new Error(
                                "El servidor no confirmó correctamente " +
                                "la configuración de ARCA."
                            );

                        }

                        window.alert(
                            datos.mensaje
                        );

                        window.location.reload();

                    }
                    catch(error){

                        window.alert(
                            error.message
                            || "No se pudo guardar la configuración de ARCA."
                        );

                        botonGuardarArca.disabled = false;

                    }

                }
            );

        }

    }
);