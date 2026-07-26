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
# RUBROS
# =========================================

class Rubro(models.Model):

    nombre = models.CharField(
        max_length=150
    )

    def __str__(self):

        return self.nombre


# =========================================
# SUBRUBROS
# =========================================

class Subrubro(models.Model):

    rubro = models.ForeignKey(
        Rubro,
        on_delete=models.CASCADE,
        related_name='subrubros'
    )

    nombre = models.CharField(
        max_length=150
    )

    def __str__(self):

        return f"{self.rubro} / {self.nombre}"


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

    rubro = models.ForeignKey(
        Rubro,
        on_delete=models.SET_NULL,
        null=True
    )

    subrubro = models.ForeignKey(
        Subrubro,
        on_delete=models.SET_NULL,
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
