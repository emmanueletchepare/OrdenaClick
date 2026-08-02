from django.db import models


# =========================================
# EMPRESAS
# =========================================

class Empresa(models.Model):

    CONDICION_FISCAL = [

        ('Responsable inscripto', 'Responsable inscripto'),
        ('Monotributo', 'Monotributo'),
        ('Exento', 'Exento'),
        ('Consumidor final', 'Consumidor final'),

    ]

    razon_social = models.CharField(
        max_length=200
    )

    nombre_fantasia = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    condicion_fiscal = models.CharField(
        max_length=50,
        choices=CONDICION_FISCAL,
        blank=True,
        null=True
    )

    cuit = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    inicio_actividades = models.DateField(
        blank=True,
        null=True
    )

    inicio_contable = models.DateField(
        blank=True,
        null=True
    )

    direccion_fiscal = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    direccion_real = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    telefono1 = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    telefono2 = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    presidente = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    vicepresidente = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    estatuto = models.FileField(
    upload_to='documentos/',
    blank=True,
    null=True
    )

    fecha_estatuto = models.DateTimeField(
         blank=True,
        null=True
    )

    acta = models.FileField(
         upload_to='documentos/',
        blank=True,
        null=True
    )

    fecha_acta = models.DateTimeField(
        blank=True,
        null=True
    )

    designacion = models.FileField(
        upload_to='documentos/',
        blank=True,
        null=True
    )

    fecha_designacion = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):

        return self.nombre_fantasia or self.razon_social


# =========================================
# EJERCICIOS CONTABLES
# =========================================

class Ejercicio(models.Model):

    ESTADOS = [

        ('Abierto', 'Abierto'),
        ('Cerrado', 'Cerrado'),

    ]

    empresa = models.ForeignKey(

        Empresa,

        on_delete=models.CASCADE,

        related_name='ejercicios'
    )

    numero = models.IntegerField()

    fecha_inicio = models.DateField()

    fecha_cierre = models.DateField()

    presidente = models.CharField(

        max_length=150,

        blank=True,

        null=True
    )

    vicepresidente = models.CharField(

        max_length=150,

        blank=True,

        null=True
    )

    estado = models.CharField(

        max_length=20,

        choices=ESTADOS,

        default='Abierto'
    )

    creado = models.DateTimeField(

        auto_now_add=True
    )

    def __str__(self):

        return f"Ejercicio {self.numero} - {self.empresa}"

# =========================================
# TIPOS DE GASTO
# =========================================

class TipoGasto(models.Model):
    """
    Clasifica el motivo económico u operativo de un gasto.

    Cada tipo de gasto pertenece exclusivamente a una empresa y puede
    relacionarse con cero, uno o varios proveedores.
    """

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="tipos_gasto"
    )

    nombre = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = [
            "nombre"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "nombre"
                ],
                name="tipo_gasto_nombre_unico_por_empresa"
            )
        ]

    def __str__(self):
        """
        Devuelve el nombre del tipo de gasto.
        """
        return self.nombre


# =========================================
# TIPOS DE GASTO - PROVEEDORES
# =========================================

class TipoGastoProveedor(models.Model):
    """
    Relación explícita entre un tipo de gasto y un proveedor.

    Se utiliza un modelo intermedio para permitir agregar en el futuro
    información como proveedor preferido, orden, vigencia u observaciones.
    """

    tipo_gasto = models.ForeignKey(
        TipoGasto,
        on_delete=models.CASCADE,
        related_name="relaciones_proveedores"
    )

    proveedor = models.ForeignKey(
        "Proveedor",
        on_delete=models.CASCADE,
        related_name="relaciones_tipos_gasto"
    )

    class Meta:
        ordering = [
            "proveedor__razon_social"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tipo_gasto",
                    "proveedor"
                ],
                name="tipo_gasto_proveedor_unico"
            )
        ]

    def __str__(self):
        """
        Devuelve una representación de la relación.
        """
        return f"{self.tipo_gasto} - {self.proveedor}"

# =========================================
# MOVIMIENTOS
# =========================================

class Movimiento(models.Model):

    ESTADOS = [

        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),

    ]

    ejercicio = models.ForeignKey(

    Ejercicio,

    on_delete=models.CASCADE,

    related_name='movimientos',

    null=True,

    blank=True
)

    tipo_gasto = models.ForeignKey(
        TipoGasto,
        on_delete=models.PROTECT,
        related_name="movimientos",
        null=True,
        blank=True
    )

    descripcion = models.CharField(
        max_length=255
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha_pago = models.DateField()

    fecha_vencimiento = models.DateField(
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    archivo = models.FileField(
        upload_to='movimientos/',
        blank=True,
        null=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        if self.ejercicio:
            return f"{self.ejercicio.empresa} - {self.descripcion}"

        return self.descripcion

class CentroOperativo(models.Model):
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='centros'
    )

    nombre = models.CharField(
        max_length=100
    )

    tipo = models.CharField(
        max_length=50,
        choices=[
            ('Casa Central', 'Casa Central'),
            ('Sucursal', 'Sucursal'),
            ('Deposito', 'Deposito'),
            ('Mostrador', 'Mostrador')
        ]
    )

    direccion = models.CharField(
        max_length=250,
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    def __str__(self):

        return self.nombre

# =========================================
# BANCOS
# =========================================

class Banco(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='bancos'
    )

    nombre = models.CharField(
        max_length=120
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:

        ordering = ['nombre']

        unique_together = (
            'empresa',
            'nombre'
        )

    def __str__(self):

        return self.nombre

# =========================================
# PROVEEDORES
# =========================================
class Proveedor(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="proveedores"
    )

    razon_social = models.CharField(
        max_length=200,
    )

    cuit = models.CharField(
        max_length=13
    )

    direccion = models.CharField(
        max_length=255,
        blank=True
    )

    localidad = models.CharField(
        max_length=120,
        blank=True
    )

    contacto1_nombre = models.CharField(
        max_length=150,
        blank=True
    )

    contacto1_telefono = models.CharField(
        max_length=50,
        blank=True
    )

    contacto1_email = models.EmailField(
        blank=True
    )

    contacto2_nombre = models.CharField(
        max_length=150,
        blank=True
    )

    contacto2_telefono = models.CharField(
        max_length=50,
        blank=True
    )

    contacto2_email = models.EmailField(
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    observaciones = models.TextField(
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:

        ordering = [
            "razon_social"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "cuit"
                ],
                name="proveedor_cuit_unico_por_empresa"
            )

        ]

    def __str__(self):

        return self.razon_social

# =========================================
# GESTIÓN DE CLAVES
# =========================================

class GestionClave(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="claves"
    )

    nombre = models.CharField(
        max_length=150
    )

    sitio = models.CharField(
        max_length=255,
        blank=True
    )

    usuario = models.CharField(
        max_length=150,
        blank=True
    )

    correo = models.EmailField(
        blank=True
    )

    contrasena_cifrada = models.TextField(
        blank=True
    )

    referencia_recuperacion_1 = models.CharField(
        max_length=255,
        blank=True
    )

    referencia_recuperacion_2 = models.CharField(
        max_length=255,
        blank=True
    )

    observaciones = models.TextField(
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            "nombre"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "empresa",
                    "nombre"
                ],
                condition=models.Q(
                    activo=True
                ),
                name="unique_gestion_clave_activa_empresa_nombre"
            )

        ]

    def __str__(self):

        return self.nombre