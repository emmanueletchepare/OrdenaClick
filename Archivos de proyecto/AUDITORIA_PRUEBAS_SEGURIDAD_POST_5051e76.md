# Auditoría de regresión de seguridad posterior a `5051e76`

**Alcance aprobado:** mantenimiento de **pruebas y documentación**, sin modificación
alguna de los servicios, endpoints, permisos, modelos, migraciones, plantillas,
JavaScript, CSS o base de datos operativa.

## Origen y diagnóstico

- En la suite de **563 pruebas** se observaron inicialmente 8 fallos, 6 errores
  y 1 prueba omitida. El caso HTTP 403 del Bloque A quedó corregido y las
  **18 pruebas dirigidas** de Alertas/Auditoría de lecturas pasaron.
- Los **6 resultados restantes de Caja** corresponden a pruebas que asumían
  que `admin_centro` recibía Caja solo por su jerarquía. La regla vigente exige
  concesión explícita y revocable de `caja.total`. Se adecuan únicamente los
  datos de prueba y se incorporan controles de denegación tras revocar.
- **Inventario B6:** el listado de parámetros de URL no contenía los conversores
  incorporados posteriormente: `empleado_id`, `caso_id`, `documento_id`,
  `operacion_id`. Se mantiene el barrido GET/POST anónimo sobre rutas privadas.
- **Gestión de claves:** los mocks apuntaban a una función de autorización
  antigua. Los tests ahora ejercitan `permiso_claves`, el filtro de claves
  propias, las cabeceras sin caché y la denegación de acceso.
- **Panel Colaborador:** la ruta histórica HTTP 302 redirige al panel unificado
  Administrar. La prueba debe validar el destino y el formulario POST+CSRF.
- **Concurrencia B9c:** pruebas exclusivas de PostgreSQL. Se marca la clase
  con una etiqueta de test para excluirla **de manera explícita** en SQLite;
  su validación real NO queda aprobada ni reemplazada por SQLite.

## Comandos de validación

Desde Casa y un entorno virtual válido:

```powershell
python manage.py check
python manage.py makemigrations usuarios --check --dry-run
python manage.py test usuarios.pruebas.test_caja1_historial_panel usuarios.pruebas.test_caja1_movimientos_operativos usuarios.pruebas.test_seguridad_empresa usuarios.pruebas.test_inventario_rutas_b6 usuarios.pruebas.test_claves_no_cache usuarios.pruebas.test_b12_seguridad_operativa
python manage.py test --exclude-tag=postgresql_only

git diff --check
git status --short
```

El último comando de suite cubre lo **ejecutable en SQLite** y declara
expresamente qué se excluyó. **No equivale a suite íntegra aprobada.**
Cuando exista una base PostgreSQL de pruebas aislada y expresamente
configurada, ejecutar las pruebas B9c según
`ordenaclick/settings_test_postgres_b9c.py` y sus variables `B9C_PG_*`,
sin apuntar jamás a una base operativa ni crearla automáticamente.

## Criterios de aceptación

- Sin disminuir requisitos de acceso de Caja ni alterar `puede` o `exigir`.
- Los tests de Caja incluyen permiso concedido, denegación y revocación.
- Las rutas privadas siguen rechazando acceso anónimo, no se excluyen del barrido.
- Claves propias y revelación solo autorizada, con `Cache-Control: no-store`.
- La ruta histórica de Colaborador mantiene su redirección; sidebar y panel
  unificado quedan intactos.
- B9c requiere PostgreSQL real; no declarar que está aprobado sin ejecutarlo.
- No publicar en producción basándose solamente en esta regresión.

**Estado:** propuesta instalada solo tras `--apply`. Registrar resultados reales
sin asumir que una prueba pasó hasta ejecutar sus comandos.
