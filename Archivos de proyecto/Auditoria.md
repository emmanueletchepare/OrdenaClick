# AUDITORIA.md --- Auditoría de OrdenaClick

**Fecha de auditoría inicial:** 13/09/2026 **Estado del proyecto:**
Desarrollo previo a Beta **Objetivo:** Mantener un registro priorizado
de riesgos, deuda técnica, problemas de experiencia de usuario y mejoras
estructurales detectadas durante el desarrollo de OrdenaClick.

------------------------------------------------------------------------

# 1. PROPÓSITO DE ESTE DOCUMENTO

Este documento no es un listado de tareas funcionales.

Para desarrollo de nuevas funciones y prioridades de producto se utiliza
`TODO.md`.

`AUDITORIA.md` registra problemas o mejoras relacionados principalmente
con:

-   seguridad;
-   integridad de datos;
-   aislamiento entre Empresas;
-   arquitectura;
-   mantenibilidad;
-   rendimiento;
-   testing;
-   backups y recuperación;
-   configuración de producción;
-   experiencia de usuario;
-   coherencia visual;
-   deuda técnica.

La auditoría debe mantenerse como **documento vivo**.

Los problemas encontrados durante el desarrollo pueden agregarse aquí
aunque no se corrijan inmediatamente.

------------------------------------------------------------------------

# 2. CRITERIO DE PRIORIDAD

No toda deuda técnica justifica detener el desarrollo funcional.

Se utilizará la siguiente clasificación:

## 🔴 CRÍTICO --- Resolver antes de utilizar datos reales / producción

Problemas que pueden provocar:

-   acceso no autorizado;
-   exposición de información;
-   pérdida o corrupción de datos;
-   operaciones financieras incorrectas;
-   acceso cruzado entre Empresas;
-   eliminación accidental;
-   falsa sensación de respaldo;
-   vulnerabilidades relevantes de seguridad.

Estos problemas bloquean la salida a producción.

------------------------------------------------------------------------

## 🟠 IMPORTANTE --- Resolver antes de cerrar Beta o al tocar el circuito afectado

Problemas que pueden:

-   generar errores funcionales;
-   provocar inconsistencias;
-   dificultar completar correctamente un circuito;
-   producir comportamientos ambiguos;
-   afectar vencimientos, saldos o estados;
-   complicar seriamente el mantenimiento inmediato.

------------------------------------------------------------------------

## 🟡 DEUDA TÉCNICA --- Refactorización posterior a Beta

Código que actualmente funciona pero:

-   es demasiado grande;
-   está duplicado;
-   mezcla responsabilidades;
-   resulta difícil de mantener;
-   tiene CSS/JavaScript inline heredado;
-   necesita mejor separación en módulos o servicios;
-   necesita optimización.

No debe provocar una reescritura prematura durante el cierre funcional
de la Beta.

------------------------------------------------------------------------

## 🟢 CORRECTO / BUENA BASE

Decisiones o implementaciones que conviene preservar y extender.

El objetivo de una refactorización no es modificar código simplemente
porque es antiguo.

**Lo que está correctamente diseñado y funciona debe conservarse.**

------------------------------------------------------------------------

# 3. CONCLUSIÓN GENERAL DE LA AUDITORÍA

Estado inicial observado:

  ---------------------------------------------------------------------
  Área                      Estado
  ------------------------- -------------------------------------------
  Concepto de producto      🟢 Bien encaminado

  Arquitectura conceptual   🟢 Bien encaminada

  Núcleo financiero         🟢 / 🟡 Buena base en evolución
  reciente                  

  Experiencia de usuario    🟡 Buena dirección, falta consolidación

  Coherencia visual         🟡 Debe seguir unificándose

  Mantenibilidad            🟡 Deuda técnica importante

  Testing                   🟡 Buena base, cobertura todavía
                            insuficiente

  Seguridad                 🔴 No apta todavía para exposición pública

  Aislamiento entre         🔴 Incompleto en código heredado
  Empresas                  

  Backup / restauración     🔴 Incompleto

  Preparación para          🔴 Pendiente
  producción                
  ---------------------------------------------------------------------

La arquitectura conceptual actual es más madura que algunas partes del
código heredado.

El principal problema no parece ser una mala concepción del sistema,
sino que **reglas arquitectónicas y de seguridad definidas
posteriormente todavía no fueron aplicadas de manera uniforme al código
anterior**.

------------------------------------------------------------------------

# 4. AUDITORÍA DE SEGURIDAD E INTEGRIDAD

## 🔴 4.1 Autorización por Empresa incompleta

### Problema

OrdenaClick establece como regla:

> Nunca confiar en IDs enviados por el frontend para determinar
> pertenencia o autorización.

Ya existe:

`usuarios/services/seguridad.py`

con una función central:

`obtener_empresa_autorizada(usuario, empresa_id)`

Sin embargo, diferentes endpoints heredados todavía reciben `empresa_id`
desde GET/POST y realizan consultas directas del tipo:

``` python
Empresa.objects.get(id=empresa_id)
```

sin verificar necesariamente que el usuario tenga acceso a esa Empresa.

Se detectaron zonas a revisar relacionadas con:

-   Bancos;
-   Cuentas bancarias;
-   Tarjetas;
-   Retenciones;
-   Centros Operativos;
-   Recursos Operativos;
-   Proveedores;
-   Tipos de Gasto;
-   Gestión de Claves;
-   otros ABM heredados.

Además, varios endpoints requieren revisión respecto de
`@login_required`.

### Riesgo

Un usuario podría intentar modificar manualmente IDs enviados por el
navegador y acceder u operar sobre información perteneciente a otra
Empresa.

### Acción futura

Realizar una auditoría endpoint por endpoint.

Cada operación debe validar como mínimo:

**Usuario → Empresa → Rol/Capacidad → Objeto**

Agregar tests específicos de acceso cruzado entre Empresas.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

## 🔴 4.2 Gestión de Claves

### Problema

Existe funcionalidad que permite recuperar una credencial almacenada,
descifrarla mediante Fernet y devolverla al frontend.

La decisión de utilizar una clave maestra externa mediante:

`ORDENACLICK_CLAVES_KEY`

es correcta.

Sin embargo, la capa de autorización necesita fortalecerse.

Particularmente debe revisarse `ver_gestion_clave()` y todos los
endpoints relacionados.

### Riesgo

Las credenciales son información especialmente sensible.

No alcanza con cifrar correctamente la información almacenada si un
endpoint puede devolverla sin autorización suficiente.

### Acción futura

Implementar:

-   autenticación obligatoria;
-   autorización por Empresa;
-   permisos/capacidad específica;
-   protección contra acceso cruzado;
-   auditoría de visualización de credenciales;
-   evaluar reautenticación para revelar una contraseña;
-   evitar exposición innecesaria en logs/respuestas.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

## 🔴 4.3 Operaciones destructivas

### Problema

Se detectaron operaciones críticas que necesitan endurecer sus
condiciones de ejecución.

En particular revisar:

`eliminar_empresa()`

y otras operaciones destructivas.

Una eliminación no debe ejecutarse mediante una simple petición GET.

### Regla

Las operaciones destructivas deben utilizar:

-   usuario autenticado;
-   autorización explícita;
-   método POST;
-   protección CSRF;
-   validaciones de negocio;
-   confirmación de usuario cuando corresponda.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

## 🔴 4.4 Exportación de Empresa sin autorización suficiente

Revisar especialmente:

`exportar_empresa()`

La exportación puede contener información empresarial y eventualmente
información personal o sensible.

Debe comprobarse que sólo usuarios expresamente autorizados puedan
realizarla.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

# 5. BACKUP, EXPORTACIÓN E IMPORTACIÓN

## 🔴 5.1 Exportar Empresa todavía no representa un backup completo

### Problema

La arquitectura definida establece que una Empresa exportada debería
poder reconstruir posteriormente su entorno.

Actualmente la exportación cubre principalmente información básica de
Empresa y determinados documentos.

No representa todavía todo el ecosistema.

Debe contemplar progresivamente:

-   Empresa;
-   Ejercicios;
-   Centros Operativos;
-   Recursos Operativos;
-   Bancos;
-   Cuentas;
-   Proveedores;
-   Tipos de Gasto;
-   Movimientos;
-   Pagos;
-   Aplicaciones de Pago;
-   Tarjetas;
-   Cheques;
-   Retenciones;
-   Planes;
-   Cuotas;
-   Vencimientos;
-   Alertas;
-   configuraciones;
-   archivos;
-   históricos;
-   inactivos;
-   futuras entidades.

### Riesgo

El usuario podría interpretar **Exportar Empresa** como un backup
completo cuando actualmente no lo es.

Una falsa sensación de respaldo puede ser peor que no ofrecer respaldo.

### Acción futura

Completar el sistema de exportación/importación antes de presentarlo
como mecanismo real de recuperación.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

## 🔴 5.2 Archivos de importación dentro del historial Git

### Problema

`.gitignore` contiene correctamente:

``` text
media/
```

Sin embargo, existen ZIP de importaciones que habían sido versionados
previamente y continúan formando parte del historial/repositorio.

Estos archivos pueden contener:

-   información empresarial;
-   CUIT;
-   domicilios;
-   emails;
-   documentación societaria;
-   autoridades;
-   documentos privados.

### Acción futura

Realizar una limpieza controlada del repositorio.

No realizar eliminaciones improvisadas del historial Git.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

## 🟠 5.3 Reconstrucción de IDs durante importación

La importación completa deberá reconstruir relaciones mediante mapas:

``` text
ID original → ID nuevo
```

No se debe asumir que los IDs de la base destino coincidirán con los
originales.

También deberá contemplarse versionado del formato de exportación.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

# 6. FECHAS, VENCIMIENTOS Y ZONA HORARIA

## 🟠 6.1 Política temporal

Actualmente la configuración utiliza:

``` python
TIME_ZONE = "UTC"
```

y existen cálculos financieros basados en fechas actuales.

OrdenaClick utiliza conceptos sensibles al día calendario:

-   vence hoy;
-   vencido;
-   próximos vencimientos;
-   alertas;
-   débitos;
-   cheques;
-   e-Cheqs;
-   acreditaciones.

### Riesgo

El día calendario del servidor puede no coincidir con el día calendario
del usuario.

### Acción futura

Definir explícitamente la política temporal de OrdenaClick.

Centralizar el concepto de **fecha actual operativa** cuando sea
necesario y evitar reglas temporales dispersas.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

# 7. CONFIGURACIÓN DE PRODUCCIÓN

## 🔴 7.1 Configuración actual de desarrollo

Actualmente existen valores apropiados para desarrollo local, entre
ellos:

``` python
DEBUG = True
ALLOWED_HOSTS = []
```

Esto no representa un problema mientras OrdenaClick continúe
ejecutándose únicamente como entorno de desarrollo.

Antes de producción deberá existir una configuración específica.

### Revisar

-   `DEBUG=False`;
-   `ALLOWED_HOSTS`;
-   HTTPS;
-   cookies seguras;
-   CSRF;
-   HSTS cuando corresponda;
-   `SECRET_KEY`;
-   secretos externos;
-   permisos de archivos;
-   almacenamiento de archivos privados;
-   logging;
-   backups;
-   recuperación ante fallos;
-   configuración de base de datos;
-   política de sesiones.

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

# 8. EXPERIENCIA DE USUARIO

## 🟢 8.1 Separación Comprobantes / Obligaciones

La separación conceptual entre:

**REGISTROS → Comprobantes**

y

**REGISTROS → Obligaciones**

es correcta.

Una obligación como:

-   sueldo;
-   aporte;
-   impuesto;
-   tasa;

no debe ser forzada dentro del modelo documental de una factura.

Ambos circuitos deben compartir el núcleo financiero cuando corresponda
sin obligar al usuario a completar información que no tiene sentido
económico.

### Decisión

**Preservar.**

------------------------------------------------------------------------

## 🟢 8.2 Navegación contextual mediante `[+]`

El patrón:

``` text
Usuario está cargando
        ↓
Necesita una entidad inexistente
        ↓
Presiona [+]
        ↓
Realiza el alta
        ↓
Vuelve al formulario original
        ↓
Conserva lo cargado
        ↓
La nueva entidad queda seleccionada
```

es una decisión importante de experiencia de usuario.

Debe mantenerse en los nuevos módulos.

### Decisión

**Preservar y reutilizar como patrón general.**

------------------------------------------------------------------------

## 🟢 8.3 OrdenaClick debe anticipar

Vencimientos y Alertas no deben convertirse simplemente en listados
administrativos.

Una de las ideas centrales del producto es:

> OrdenaClick no sólo registra lo que ocurrió. También ayuda al usuario
> a anticipar lo que debe hacer.

Las distintas interfaces deben consumir una fuente financiera común y no
implementar reglas independientes.

### Decisión

**Preservar.**

------------------------------------------------------------------------

## 🟡 8.4 Uniformidad visual

OrdenaClick debe sentirse como una única aplicación.

Los nuevos formularios no deben introducir arbitrariamente:

-   nuevos estilos de botones;
-   espaciados diferentes;
-   modales incompatibles;
-   mensajes distintos;
-   navegación diferente;
-   nuevos patrones sin necesidad.

Antes de crear una pantalla nueva debe identificarse qué pantalla
existente sirve como referencia visual.

Los ABM de **Bancos** y **Centros Operativos** constituyen referencias
importantes del lenguaje visual actual.

### Regla

Una funcionalidad técnicamente correcta pero visualmente ajena al resto
de OrdenaClick debe considerarse incompleta.

### Estado

-   [ ] Revisar progresivamente

------------------------------------------------------------------------

## 🟡 8.5 Densidad del Panel Administrativo

`panel_admin.html` concentra una gran cantidad de funcionalidad.

Esto actualmente permite conservar contexto, pero puede provocar
progresivamente:

-   exceso de información;
-   navegación compleja;
-   pantallas extensas;
-   dificultad de mantenimiento;
-   sensación de sistema pesado.

No dividir prematuramente.

Evaluar durante la etapa posterior a Beta qué funciones merecen:

-   pantalla propia;
-   componente;
-   modal;
-   navegación específica;
-   template parcial.

### Estado

-   [ ] Post-Beta

------------------------------------------------------------------------

# 9. ARQUITECTURA Y MANTENIBILIDAD

## 🟡 9.1 `usuarios/views.py` excesivamente grande

Se observó un archivo `views.py` de aproximadamente 10.500 líneas.

Algunas funciones concentran una cantidad muy elevada de lógica.

Entre ellas:

-   `guardar_movimiento()`;
-   `actualizar_movimiento()`;
-   `registrar_debito_automatico_movimiento()`.

### Problemas

Esto dificulta:

-   comprensión;
-   testing aislado;
-   mantenimiento;
-   revisión;
-   reutilización;
-   detección de efectos secundarios;
-   modificación segura.

### Estrategia

**No realizar un refactor masivo antes de cerrar Beta.**

Cuando se toque una zona:

1.  identificar reglas reutilizables;
2.  moverlas progresivamente a servicios;
3.  mantener vistas orientadas a HTTP/orquestación;
4.  agregar tests antes de modificaciones de alto riesgo.

Después de Beta realizar una refactorización estructural planificada.

### Estado

-   [ ] Post-Beta / progresivo

------------------------------------------------------------------------

## 🟡 9.2 `panel_admin.html` excesivamente grande

El template principal contiene aproximadamente 19.600 líneas.

Concentra:

-   estructura HTML;
-   formularios;
-   diferentes módulos;
-   comportamiento heredado;
-   CSS/JS inline existente.

### Estrategia

No reescribir durante el cierre funcional de Beta.

Extraer progresivamente cuando se toque cada pantalla.

### Estado

-   [ ] Post-Beta / progresivo

------------------------------------------------------------------------

## 🟡 9.3 CSS y JavaScript inline heredados

Existe código inline anterior a las reglas actuales.

### Regla

No agregar nuevo CSS/JS inline.

Al modificar una pantalla existente:

-   extraer progresivamente lo relacionado cuando resulte razonable;
-   evitar refactors masivos sin beneficio inmediato;
-   utilizar archivos estáticos compartidos;
-   conservar comportamiento existente.

### Estado

-   [ ] Progresivo

------------------------------------------------------------------------

## 🟡 9.4 Duplicaciones menores

Se detectaron pequeñas duplicaciones, por ejemplo constantes financieras
repetidas dentro de servicios.

No representan riesgo inmediato.

Deben eliminarse durante tareas de saneamiento.

### Estado

-   [ ] Post-Beta / oportunidad

------------------------------------------------------------------------

# 10. NÚCLEO FINANCIERO

## 🟢 10.1 Separación Movimiento / Pago / AplicacionPago

La arquitectura:

``` text
Movimiento
    ↓
AplicacionPago
    ↑
Pago
```

constituye una buena base.

Permite representar correctamente:

-   pagos parciales;
-   múltiples pagos;
-   pagos distribuidos;
-   saldos;
-   planes;
-   retenciones;
-   intereses;
-   futuros saldos a cuenta;
-   Orden de Pago;
-   cheques/e-Cheqs;
-   reportes financieros.

### Decisión

**Preservar.**

No volver a colocar la forma de pago directamente en `Movimiento` como
única fuente de verdad financiera.

------------------------------------------------------------------------

## 🟢 10.2 Servicios financieros

La existencia de:

`usuarios/services/financiero.py`

es una buena dirección arquitectónica.

Actualmente centraliza progresivamente conceptos como:

-   saldo;
-   total aplicado;
-   estado financiero;
-   vencimientos;
-   alertas;
-   validación de importes;
-   creación financiera reutilizable.

### Estrategia

Extender esta arquitectura.

Evitar implementar nuevamente estas reglas dentro de:

-   vistas;
-   JavaScript;
-   templates;
-   nuevos módulos.

### Estado

-   [x] Buena base existente
-   [ ] Continuar centralización progresiva

------------------------------------------------------------------------

## 🟢 10.3 Restricciones de integridad

Existen restricciones de base de datos en modelos financieros,
especialmente en `AplicacionPago`, que protegen determinadas reglas
independientemente del frontend.

Esto es correcto.

### Regla

Las reglas críticas de integridad no deben depender exclusivamente de
JavaScript o formularios.

### Estado

-   [x] Buena base existente

------------------------------------------------------------------------

# 11. DEPENDENCIAS Y REPRODUCIBILIDAD

## 🟡 11.1 Falta manifiesto formal de dependencias

No se observó en la raíz un mecanismo estándar como:

-   `requirements.txt`;
-   `pyproject.toml`;
-   `Pipfile`;
-   lock equivalente.

El entorno `venv` local no debe considerarse una definición reproducible
del proyecto.

### Objetivo

Una instalación nueva debería poder realizar:

``` text
Instalar Python
        ↓
Instalar dependencias declaradas
        ↓
Configurar variables de entorno
        ↓
Ejecutar migraciones
        ↓
Ejecutar tests
        ↓
Iniciar OrdenaClick
```

sin copiar el entorno virtual de desarrollo.

### Estado

-   [ ] Antes de despliegue

------------------------------------------------------------------------

# 12. TESTING

## 🟡 12.1 Estado actual

Existe una base de tests que cubre, entre otros conceptos:

-   saldo sin pagos;
-   pago parcial;
-   pago total;
-   múltiples aplicaciones;
-   retenciones;
-   intereses por mora;
-   vencimientos;
-   alertas;
-   seguridad básica de Empresa;
-   Próximos Vencimientos.

La última ejecución conocida antes de esta auditoría fue:

``` text
Ran 27 tests
OK
```

Esto constituye una buena base, pero no una cobertura suficiente para
producción.

------------------------------------------------------------------------

## 🔴 12.2 Tests de aislamiento entre Empresas

Los tests actuales no recorren todavía todos los endpoints heredados.

Deben agregarse pruebas específicas intentando:

``` text
Usuario Empresa A
        ↓
envía manualmente ID Empresa B
        ↓
backend rechaza operación
```

Esto debe probarse para:

-   lectura;
-   alta;
-   modificación;
-   eliminación;
-   exportación;
-   descarga;
-   claves;
-   operaciones financieras.

### Estado

-   [ ] Pendiente antes de producción

------------------------------------------------------------------------

## 🟠 12.3 Tests financieros de integración

Antes de Beta deben probarse circuitos completos y no solamente
funciones aisladas.

Especialmente:

``` text
Comprobante
→ Vencimiento
→ Pago parcial
→ Segundo pago
→ Saldo
→ Estado
→ Alerta
```

y posteriormente:

``` text
Obligación
→ Orden de Pago
→ Pago
→ AplicacionPago
→ Caja
→ Cheque/e-Cheq
→ Saldo
→ Vencimiento
```

### Estado

-   [ ] Pendiente

------------------------------------------------------------------------

# 13. ESTRATEGIA DE REFACTORIZACIÓN

La refactorización general se realizará **después de obtener una Beta
funcional estable**.

Hasta entonces:

-   corregir inmediatamente riesgos de datos/seguridad;
-   corregir errores funcionales;
-   centralizar reglas nuevas correctamente;
-   evitar introducir nueva deuda innecesaria;
-   no detener el desarrollo por deuda técnica puramente estética.

Una vez cerrada la Beta:

## Fase de estabilización

1.  Congelar temporalmente nuevas funciones.
2.  Ampliar cobertura de tests.
3.  Refactorizar arquitectura.
4.  Separar responsabilidades.
5.  Reducir `views.py`.
6.  Reducir templates monolíticos.
7.  Centralizar reglas financieras.
8.  Eliminar duplicaciones.
9.  Extraer CSS/JS inline restante.
10. Optimizar consultas.
11. Revisar transacciones.
12. Auditar permisos.
13. Auditar seguridad.
14. Auditar archivos privados.
15. Revisar logs.
16. Completar backup/restauración.
17. Preparar configuración de producción.
18. Realizar pruebas integrales.
19. Revisar rendimiento.
20. Realizar auditoría final de UX y coherencia visual.

------------------------------------------------------------------------

# 14. PRINCIPIO DE REFACTORIZACIÓN

Refactorizar OrdenaClick **no significa reescribir OrdenaClick**.

La Beta debe demostrar qué comportamiento funciona correctamente para el
usuario.

La etapa posterior deberá:

> conservar el comportamiento validado y mejorar su implementación
> interna.

Objetivos:

-   código más claro;
-   mayor modularidad;
-   mayor seguridad;
-   mejor testing;
-   mejor rendimiento;
-   menor riesgo de regresiones;
-   mantenimiento más sencillo.

------------------------------------------------------------------------

# 15. PRINCIPIO DE EXPERIENCIA DE USUARIO

Toda funcionalidad debe responder a una pregunta:

> **¿Esto le resuelve trabajo al usuario o le agrega trabajo?**

OrdenaClick debe intentar:

-   reducir pasos;
-   evitar cargas redundantes;
-   conservar contexto;
-   anticipar obligaciones;
-   mostrar información comprensible;
-   evitar decisiones técnicas visibles innecesariamente;
-   mantener un lenguaje visual uniforme;
-   prevenir errores antes de que ocurran;
-   permitir corregir errores sin destruir historia.

La calidad técnica y la experiencia de usuario no son objetivos
separados.

------------------------------------------------------------------------

# 16. CRITERIO PARA NUEVAS FUNCIONES

Antes de desarrollar una nueva función:

1.  revisar `VISION.md`;
2.  revisar `REGLAS.md`;
3.  revisar `ARQUITECTURA.md`;
4.  revisar `MODELO_DATOS.md`;
5.  revisar `DECISIONES.md`;
6.  revisar `FLUJO_NAVEGACION.md`;
7.  revisar este `AUDITORIA.md` si afecta una zona con riesgo conocido.

Antes de crear una nueva regla financiera:

> comprobar si ya existe en `services/`.

Antes de crear un nuevo patrón visual:

> comprobar si OrdenaClick ya tiene uno equivalente.

Antes de confiar en un ID recibido del navegador:

> validar usuario y Empresa en backend.

------------------------------------------------------------------------

# 17. REGLA DE TRABAJO DURANTE EL DESARROLLO

Cuando una modificación sea extensa o tenga riesgo de romper
comportamiento existente:

-   reemplazar funciones completas cuando resulte más seguro que editar
    fragmentos;
-   indicar siempre archivo exacto;
-   indicar función, clase, selector o bloque exacto;
-   explicar qué se reemplaza;
-   evitar cambios colaterales no relacionados;
-   probar después del cambio.

No realizar refactors oportunistas bajo la lógica de:

> "ya que estamos..."

salvo que sean necesarios para:

-   integridad;
-   seguridad;
-   corrección funcional;
-   cumplimiento de una regla arquitectónica imprescindible.

------------------------------------------------------------------------

# 18. FOTO INICIAL DE LA AUDITORÍA

La auditoría inicial concluye:

### Como auditor

OrdenaClick **todavía no debe exponerse públicamente con datos reales**.

El principal bloqueo actual es completar:

-   autenticación;
-   autorización;
-   aislamiento por Empresa;
-   protección de operaciones críticas;
-   seguridad de Gestión de Claves;
-   backup/restauración real;
-   configuración de producción.

### Como usuario

OrdenaClick está desarrollando una identidad funcional clara.

Sus puntos fuertes actuales son:

-   conservar contexto;
-   evitar carga innecesaria;
-   anticipar vencimientos;
-   separar correctamente diferentes realidades económicas;
-   integrar los circuitos mediante un núcleo financiero común.

La uniformidad visual y de interacción debe mantenerse como requisito de
toda nueva pantalla.

### Como desarrollador

Existe deuda técnica considerable, especialmente por archivos y
funciones monolíticas.

Sin embargo, no se recomienda una reescritura inmediata.

El núcleo financiero reciente y la progresiva incorporación de
`services/` proporcionan una base razonable para continuar hasta cerrar
la Beta.

------------------------------------------------------------------------

# 19. OBJETIVO FINAL

El objetivo no es solamente que OrdenaClick funcione.

El objetivo es llegar a una aplicación que:

**funcione correctamente, sea intuitiva, proteja los datos del usuario,
conserve la historia financiera, pueda recuperarse ante fallos y sea
mantenible a medida que crece.**

La secuencia elegida es:

``` text
Cerrar funcionalidad Beta
        ↓
Estabilizar
        ↓
Refactorizar
        ↓
Auditar seguridad e integridad
        ↓
Optimizar
        ↓
Pruebas integrales
        ↓
Preparar producción
```

La velocidad de desarrollo es importante.

**La confianza del usuario en sus datos es más importante.**

------------------------------------------------------------------------

# ACTUALIZACIÓN 17/09/2026 --- EDICIÓN, PAGOS Y OPERACIONES DESTRUCTIVAS

Esta actualización complementa la auditoría inicial y no reemplaza sus
riesgos pendientes.

## Avances

Se incorporaron centralización de validaciones financieras, autorización
por Empresa en endpoints financieros nuevos, transacciones/bloqueos
principales, validación backend de sobreaplicación, múltiples Pagos en
edición y congelamiento estructural con historia financiera.

Al 17/09/2026 la suite verificada alcanza **45 tests OK** tras los
primeros tests de eliminación de Pago.

## Movimiento con historia financiera

Una `AplicacionPago` histórica impide reescribir estructura
económica/documental y también impide la baja física del Movimiento.
Sólo permanecen editables factura/archivo, forma prevista/cuenta válida
y nuevos Pagos contra saldo. Backend continúa siendo autoridad.

## Baja física de Movimiento

Un Movimiento cargado por error y sin aplicaciones puede eliminarse
físicamente. Con cualquier `AplicacionPago` debe rechazarse,
independientemente del medio de pago. La implementación pendiente debe
usar autenticación, Empresa autorizada, `POST`, CSRF, transacción,
bloqueo, comprobación de aplicaciones y eliminación explícita de
dependencias derivadas.

## Riesgo importante pendiente: eliminación/reversión de Pago

Existe backend inicial, pero el circuito no está cerrado. Antes de
conectarlo definitivamente a interfaz deben verificarse: 1.
sincronización de Vencimiento cuando reaparece saldo; 2. sincronización
de Alertas; 3. atomicidad completa; 4. concurrencia de instrumentos cuyo
estado pueda cambiar; 5. consecuencias posteriores de componentes
financieros; 6. cuándo no es seguro borrar y corresponde reversión
histórica.

Esto protege al Pago; no crea excepciones por medio de pago para
eliminar el Movimiento.

## UX acordada

Los Pagos históricos aparecen dentro de la edición del Movimiento con
acción de gestión/lápiz. Un Pago incorrecto se corrige mediante
eliminación/reversión controlada, no reescritura silenciosa. Tras
corregir, la pantalla refresca desde backend. Al retirar la última
aplicación reaparece el saldo, se recalculan
estados/Vencimientos/Alertas, se desbloquea la estructura y el
Movimiento puede eliminarse si era un error de carga.

Se mantienen los criterios: \> ¿Esto le resuelve trabajo al usuario o le
agrega trabajo?

> Refactorizar OrdenaClick no significa reescribir OrdenaClick.

------------------------------------------------------------------------

# ANEXO --- RIESGOS A CONTROLAR AL IMPLEMENTAR CAJA / CARTERA

La futura implementación de Caja, Cartera y Orden de Pago deberá evitar
que la interfaz considere `EnCartera` como sinónimo de
`disponible para pagar`. La disponibilidad depende también del
instrumento y de su condición de circulación.

Riesgos a cubrir con reglas backend y tests:

-   impedir utilizar en Pago un cheque físico `No a la orden`;
-   distinguir endoso de cesión para e-Cheqs;
-   evitar doble utilización simultánea del mismo valor de Cartera;
-   bloquear carreras entre depósito y utilización en Pago;
-   conservar trazabilidad de Cliente, Centro Operativo y destino del
    valor;
-   mantener Vencimiento/Alerta coherentes cuando el valor sale de
    Cartera;
-   pasar a vencido el valor que agota la ventana de 30 días sin salida;
-   no destruir un cheque/e-Cheq de tercero al corregir un Pago si debe
    volver a Cartera;
-   separar instrumentos propios emitidos de activos de terceros en
    Cartera;
-   diseñar el rechazo sin reescribir silenciosamente la historia del
    instrumento original.

Estas condiciones deben resolverse con autorización por Empresa,
`transaction.atomic()`, bloqueos adecuados (`select_for_update()` cuando
corresponda) y validación de negocio en backend.
