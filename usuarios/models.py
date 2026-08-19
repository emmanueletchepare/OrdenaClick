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

    centro_operativo = models.ForeignKey(
        'CentroOperativo',
        on_delete=models.PROTECT,
        related_name='movimientos',
        null=True,
        blank=True
    )

    recurso_operativo = models.ForeignKey(
        'RecursoOperativo',
        on_delete=models.PROTECT,
        related_name='movimientos',
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

    fecha_registro = models.DateField()

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

# =========================================
# PAGOS
# =========================================

class Pago(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='pagos'
    )

    fecha = models.DateField()

    importe_efectivo = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    observaciones = models.TextField(
        blank=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"Pago {self.id} - "
            f"{self.fecha}"
        )

# =========================================
# APLICACIONES DE PAGO
# =========================================

class AplicacionPago(models.Model):

    pago = models.ForeignKey(
        Pago,
        on_delete=models.PROTECT,
        related_name='aplicaciones'
    )

    movimiento = models.ForeignKey(
        Movimiento,
        on_delete=models.PROTECT,
        related_name='aplicaciones_pago',
        blank=True,
        null=True
    )

    cuota = models.ForeignKey(
        'CuotaPlan',
        on_delete=models.PROTECT,
        related_name='aplicaciones_pago',
        blank=True,
        null=True
    )

    importe = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        constraints = [

            models.CheckConstraint(
                condition=(
                    models.Q(
                        movimiento__isnull=False,
                        cuota__isnull=True
                    )
                    |
                    models.Q(
                        movimiento__isnull=True,
                        cuota__isnull=False
                    )
                ),
                name='aplicacion_pago_un_solo_destino'
            ),

            models.CheckConstraint(
                condition=models.Q(
                    importe__gt=0
                ),
                name='aplicacion_pago_importe_positivo'
            ),

        ]

    def __str__(self):

        return (
            f"Aplicación {self.id} - "
            f"{self.importe}"
        )

# =========================================
# TRANSFERENCIAS DE PAGO
# =========================================

class OperacionBancariaPago(models.Model):

    TIPOS_OPERACION = [

        (
            'Transferencia',
            'Transferencia'
        ),

        (
            'Deposito',
            'Depósito'
        ),

    ]

    MONEDAS = [

        (
            'ARS',
            'Pesos'
        ),

        (
            'USD',
            'Dólares'
        ),

    ]


    pago = models.ForeignKey(

        Pago,

        on_delete=models.PROTECT,

        related_name='operaciones_bancarias'

    )


    tipo_operacion = models.CharField(

        max_length=20,

        choices=TIPOS_OPERACION,

        default='Transferencia'

    )


    cuenta_origen = models.ForeignKey(

        'CuentaBancaria',

        on_delete=models.PROTECT,

        related_name='operaciones_pago_origen',

        blank=True,

        null=True

    )


    banco_destino = models.ForeignKey(

        'Banco',

        on_delete=models.PROTECT,

        related_name='operaciones_pago_destino'

    )


    referencia_destino = models.CharField(

        max_length=150,

        blank=True

    )


    moneda = models.CharField(

        max_length=10,

        choices=MONEDAS,

        default='ARS'

    )


    importe = models.DecimalField(

        max_digits=14,

        decimal_places=2

    )


    fecha = models.DateField()


    comprobante = models.FileField(

        upload_to='pagos/operaciones_bancarias/',

        blank=True,

        null=True

    )


    observaciones = models.TextField(

        blank=True

    )


    creado = models.DateTimeField(

        auto_now_add=True

    )


    def clean(self):

        from django.core.exceptions import ValidationError


        if(
            self.tipo_operacion ==
            'Transferencia' and
            not self.cuenta_origen
        ):

            raise ValidationError({

                'cuenta_origen':
                    'Una transferencia debe tener una cuenta bancaria de origen.'

            })


        if(
            self.tipo_operacion ==
            'Deposito' and
            self.cuenta_origen
        ):

            raise ValidationError({

                'cuenta_origen':
                    'Un depósito no debe tener una cuenta bancaria de origen. Su origen es Caja.'

            })


    def __str__(self):

        return (

            f"{self.get_tipo_operacion_display()} "
            f"{self.id} - "
            f"{self.importe} "
            f"{self.moneda}"

        )


# =========================================
# DÉBITOS AUTOMÁTICOS DE PAGO
# =========================================

class DebitoAutomaticoPago(models.Model):

    pago = models.ForeignKey(
        Pago,
        on_delete=models.PROTECT,
        related_name='debitos_automaticos'
    )

    cuenta_bancaria = models.ForeignKey(
        'CuentaBancaria',
        on_delete=models.PROTECT,
        related_name='debitos_automaticos_pago'
    )

    importe = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    fecha_debito = models.DateField()

    referencia = models.CharField(
        max_length=150,
        blank=True
    )

    comprobante = models.FileField(
        upload_to='pagos/debitos_automaticos/',
        blank=True,
        null=True
    )

    observaciones = models.TextField(
        blank=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"Débito automático {self.id} - "
            f"{self.importe}"
        )

# =========================================
# TARJETAS DE PAGO
# =========================================

class TarjetaPago(models.Model):

    pago = models.ForeignKey(
        Pago,
        on_delete=models.PROTECT,
        related_name='tarjetas'
    )


    tarjeta = models.ForeignKey(
        'Tarjeta',
        on_delete=models.PROTECT,
        related_name='operaciones_pago',
    )


    fecha = models.DateField()


    importe = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )


    cuotas = models.PositiveIntegerField(
        default=1
    )


    intereses_financiacion = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )


    referencia = models.CharField(
        max_length=150,
        blank=True
    )


    comprobante = models.FileField(
        upload_to='pagos/tarjetas/',
        blank=True,
        null=True
    )


    observaciones = models.TextField(
        blank=True
    )


    creado = models.DateTimeField(
        auto_now_add=True
    )


    def clean(self):

        from django.core.exceptions import ValidationError


        if(
            self.importe is not None and
            self.importe <= 0
        ):

            raise ValidationError({

                'importe':
                    'El importe aplicado debe ser mayor a cero.'

            })


        if(
            self.intereses_financiacion is not None and
            self.intereses_financiacion < 0
        ):

            raise ValidationError({

                'intereses_financiacion':
                    'Los intereses no pueden ser negativos.'

            })


        if(
            self.tarjeta_id and
            self.pago_id and
            self.tarjeta.empresa_id !=
            self.pago.empresa_id
        ):

            raise ValidationError({

                'tarjeta':
                    'La tarjeta debe pertenecer a la misma empresa que el pago.'

            })


        if(
            self.tarjeta_id and
            self.tarjeta.tipo_tarjeta ==
            'Debito'
        ):

            if self.cuotas != 1:

                raise ValidationError({

                    'cuotas':
                        'Una operación con tarjeta de débito debe registrarse en una sola cuota.'

                })


            if self.intereses_financiacion != 0:

                raise ValidationError({

                    'intereses_financiacion':
                        'Una operación con tarjeta de débito no debe registrar intereses de financiación.'

                })


    def __str__(self):

        return (
            f"{self.tarjeta.nombre} - "
            f"Pago {self.pago_id} - "
            f"{self.importe}"
        )


# =========================================
# RETENCIONES DE PAGO
# =========================================

class RetencionPago(models.Model):

    pago = models.ForeignKey(
        Pago,
        on_delete=models.PROTECT,
        related_name='retenciones'
    )

    tipo = models.CharField(
        max_length=100
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    comprobante = models.FileField(
        upload_to='pagos/retenciones/',
        blank=True,
        null=True
    )

    observaciones = models.TextField(
        blank=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.tipo} - "
            f"{self.importe}"
        )

# =========================================
# CHEQUES / E-CHEQS
# =========================================

class Cheque(models.Model):

    TIPOS_INSTRUMENTO = [

        ('Cheque', 'Cheque físico'),
        ('ECheq', 'e-Cheq'),

    ]

    ORIGENES = [

        ('Propio', 'Propio'),
        ('Tercero', 'Tercero'),

    ]

    TIPOS_CHEQUE = [

        ('Comun', 'Cheque Común'),
        ('Diferido', 'Cheque Diferido'),

    ]

    ESTADOS = [

        ('Pendiente', 'Pendiente'),
        ('EnCartera', 'En cartera'),
        ('Entregado', 'Entregado'),
        ('Depositado', 'Depositado'),
        ('Cobrado', 'Cobrado'),
        ('Debitado', 'Debitado'),
        ('Vencido', 'Vencido'),
        ('Rechazado', 'Rechazado'),
        ('Devuelto', 'Devuelto'),
        ('Anulado', 'Anulado'),

    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='cheques'
    )

    pago = models.ForeignKey(
        Pago,
        on_delete=models.PROTECT,
        related_name='cheques',
        blank=True,
        null=True
    )

    tipo_instrumento = models.CharField(
        max_length=20,
        choices=TIPOS_INSTRUMENTO
    )

    origen = models.CharField(
        max_length=20,
        choices=ORIGENES
    )

    tipo_cheque = models.CharField(
        max_length=20,
        choices=TIPOS_CHEQUE
    )

    banco = models.ForeignKey(
        'Banco',
        on_delete=models.PROTECT,
        related_name='cheques',
        blank=True,
        null=True
    )

    cuenta_bancaria = models.ForeignKey(
        'CuentaBancaria',
        on_delete=models.PROTECT,
        related_name='cheques',
        blank=True,
        null=True
    )

    numero = models.CharField(
        max_length=30
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha_emision = models.DateField()

    fecha_acreditacion = models.DateField(
        blank=True,
        null=True
    )

    quien_entrega = models.CharField(
        max_length=200,
        blank=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    comprobante = models.FileField(
        upload_to='pagos/cheques/',
        blank=True,
        null=True
    )

    observaciones = models.TextField(
        blank=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.get_tipo_instrumento_display()} "
            f"{self.numero} - "
            f"{self.importe}"
        )

# =========================================
# PLANES DE PAGO
# =========================================

class PlanPago(models.Model):

    PERIODICIDADES = [

        ('Mensual', 'Mensual'),
        ('Quincenal', 'Quincenal'),
        ('Semanal', 'Semanal'),
        ('Otra', 'Otra'),

    ]

    MODALIDADES_PAGO = [

        ('Manual', 'Pago manual'),
        ('DebitoAutomatico', 'Débito automático'),

    ]

    ESTADOS = [

        ('Activo', 'Activo'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),

    ]

    movimiento = models.OneToOneField(
        Movimiento,
        on_delete=models.PROTECT,
        related_name='plan_pago'
    )

    saldo_original = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    cantidad_cuotas = models.PositiveIntegerField()

    fecha_primer_vencimiento = models.DateField()

    periodicidad = models.CharField(
        max_length=20,
        choices=PERIODICIDADES,
        default='Mensual'
    )

    modalidad_pago = models.CharField(
        max_length=30,
        choices=MODALIDADES_PAGO,
        default='Manual'
    )

    cuenta_debito = models.ForeignKey(
        'CuentaBancaria',
        on_delete=models.PROTECT,
        related_name='planes_debito_automatico',
        blank=True,
        null=True
    )

    referencia_debito = models.CharField(
        max_length=150,
        blank=True
    )

    tasa_interes = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0
    )

    porcentaje_impuesto = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0
    )

    observaciones = models.TextField(
        blank=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Activo'
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return (
            f"Plan {self.id} - "
            f"{self.movimiento}"
        )


# =========================================
# CUOTAS DE PLAN
# =========================================

class CuotaPlan(models.Model):

    ESTADOS = [

        ('Pendiente', 'Pendiente'),
        ('Parcial', 'Parcial'),
        ('Pagada', 'Pagada'),
        ('Vencida', 'Vencida'),
        ('Cancelada', 'Cancelada'),

    ]

    plan = models.ForeignKey(
        PlanPago,
        on_delete=models.PROTECT,
        related_name='cuotas'
    )

    numero = models.PositiveIntegerField()

    capital = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    interes = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    impuesto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    punitorios = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    fecha_vencimiento = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            'numero'
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    'plan',
                    'numero'
                ],
                name='cuota_numero_unico_por_plan'
            )

        ]

    @property
    def total(self):

        return (
            self.capital +
            self.interes +
            self.impuesto +
            self.punitorios
        )

    def __str__(self):

        return (
            f"Cuota {self.numero} - "
            f"Plan {self.plan_id}"
        )

# =========================================
# VENCIMIENTOS
# =========================================

class Vencimiento(models.Model):

    TIPOS_ORIGEN = [

        ('Movimiento', 'Movimiento'),
        ('CuotaPlan', 'Cuota de plan'),
        ('Cheque', 'Cheque / e-Cheq'),

    ]

    ESTADOS = [

        ('Pendiente', 'Pendiente'),
        ('Parcial', 'Parcial'),
        ('Pagado', 'Pagado'),
        ('Vencido', 'Vencido'),
        ('Cancelado', 'Cancelado'),

    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='vencimientos'
    )

    tipo_origen = models.CharField(
        max_length=30,
        choices=TIPOS_ORIGEN
    )

    movimiento = models.ForeignKey(
        Movimiento,
        on_delete=models.PROTECT,
        related_name='vencimientos',
        blank=True,
        null=True
    )

    cuota = models.ForeignKey(
        CuotaPlan,
        on_delete=models.PROTECT,
        related_name='vencimientos',
        blank=True,
        null=True
    )

    cheque = models.ForeignKey(
        Cheque,
        on_delete=models.PROTECT,
        related_name='vencimientos',
        blank=True,
        null=True
    )

    fecha_vencimiento = models.DateField()

    importe_original = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    importe_pendiente = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Pendiente'
    )

    banco = models.ForeignKey(
        'Banco',
        on_delete=models.PROTECT,
        related_name='vencimientos',
        blank=True,
        null=True
    )

    cuenta_bancaria = models.ForeignKey(
        'CuentaBancaria',
        on_delete=models.PROTECT,
        related_name='vencimientos',
        blank=True,
        null=True
    )

    descripcion = models.CharField(
        max_length=255
    )

    observaciones = models.TextField(
        blank=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            'fecha_vencimiento',
            'id'
        ]

        constraints = [

            models.CheckConstraint(
                condition=(
                    models.Q(
                        movimiento__isnull=False,
                        cuota__isnull=True,
                        cheque__isnull=True
                    )
                    |
                    models.Q(
                        movimiento__isnull=True,
                        cuota__isnull=False,
                        cheque__isnull=True
                    )
                    |
                    models.Q(
                        movimiento__isnull=True,
                        cuota__isnull=True,
                        cheque__isnull=False
                    )
                ),
                name='vencimiento_un_solo_origen'
            )

        ]

    def __str__(self):

        return (
            f"{self.descripcion} - "
            f"{self.fecha_vencimiento}"
        )

# =========================================
# ALERTAS
# =========================================

class Alerta(models.Model):

    ESTADOS = [

        ('Activa', 'Activa'),
        ('Atendida', 'Atendida'),
        ('Reprogramada', 'Reprogramada'),
        ('Cancelada', 'Cancelada'),

    ]

    vencimiento = models.ForeignKey(
        Vencimiento,
        on_delete=models.PROTECT,
        related_name='alertas'
    )

    fecha_alerta = models.DateField()

    dias_anticipacion = models.PositiveIntegerField(
        default=3
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='Activa'
    )

    observaciones = models.TextField(
        blank=True
    )

    atendida_en = models.DateTimeField(
        blank=True,
        null=True
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    modificado = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = [
            'fecha_alerta',
            'id'
        ]

    def __str__(self):

        return (
            f"Alerta - "
            f"{self.vencimiento}"
        )

# =========================================
# CENTRO OPERATIVO
# =========================================

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
# RECURSOS OPERATIVOS
# =========================================

class RecursoOperativo(models.Model):

    TIPOS_RECURSO = [

        ('Persona', 'Persona'),
        ('Vehiculo', 'Vehículo'),
        ('Inmueble', 'Inmueble'),
        ('Equipo', 'Equipo'),
        ('Otro', 'Otro'),

    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='recursos_operativos'
    )

    nombre = models.CharField(
        max_length=120
    )

    tipo_recurso = models.CharField(
        max_length=20,
        choices=TIPOS_RECURSO
    )

    descripcion = models.TextField(
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:

        ordering = [
            'tipo_recurso',
            'nombre'
        ]

    def __str__(self):

        return self.nombre

class RecursoOperativoCentro(models.Model):

    recurso_operativo = models.ForeignKey(
        RecursoOperativo,
        on_delete=models.CASCADE,
        related_name="relaciones_centros"
    )

    centro_operativo = models.ForeignKey(
        CentroOperativo,
        on_delete=models.PROTECT,
        related_name="relaciones_recursos"
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "recurso_operativo",
                    "centro_operativo"
                ],
                name="recurso_operativo_centro_unico"
            )

        ]


    def __str__(self):

        return (
            f"{self.recurso_operativo} - "
            f"{self.centro_operativo}"
        )

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
# CUENTAS BANCARIAS
# =========================================

class CuentaBancaria(models.Model):

    TIPOS_CUENTA = [

        ('CuentaCorriente', 'Cuenta corriente'),
        ('CajaAhorro', 'Caja de ahorro'),
        ('Otra', 'Otra'),

    ]

    MONEDAS = [

        ('ARS', 'Pesos'),
        ('USD', 'Dólares'),

    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='cuentas_bancarias'
    )

    banco = models.ForeignKey(
        Banco,
        on_delete=models.PROTECT,
        related_name='cuentas'
    )

    nombre = models.CharField(
        max_length=120
    )

    tipo_cuenta = models.CharField(
        max_length=30,
        choices=TIPOS_CUENTA
    )

    moneda = models.CharField(
        max_length=10,
        choices=MONEDAS,
        default='ARS'
    )

    numero_cuenta = models.CharField(
        max_length=80,
        blank=True
    )

    cbu = models.CharField(
        max_length=22,
        blank=True
    )

    alias = models.CharField(
        max_length=100,
        blank=True
    )

    dias_aviso_cheques_propios = models.PositiveIntegerField(
        default=3
    )

    activo = models.BooleanField(
        default=True
    )

    def __str__(self):

        return (
            f"{self.banco.nombre} - "
            f"{self.nombre}"
        )

# =========================================
# TARJETAS
# =========================================

class Tarjeta(models.Model):

    TIPOS_TARJETA = [

        (
            'Credito',
            'Crédito'
        ),

        (
            'Debito',
            'Débito'
        ),

    ]


    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='tarjetas'
    )


    nombre = models.CharField(
        max_length=120
    )


    tipo_tarjeta = models.CharField(
        max_length=20,
        choices=TIPOS_TARJETA
    )


    cuenta_bancaria = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='tarjetas'
    )


    activo = models.BooleanField(
        default=True
    )


    class Meta:

        ordering = [
            'nombre'
        ]


        constraints = [

            models.UniqueConstraint(
                fields=[
                    'empresa',
                    'nombre'
                ],
                name='tarjeta_empresa_nombre_unico'
            ),

        ]


    def clean(self):

        from django.core.exceptions import ValidationError


        if(
            self.cuenta_bancaria_id and
            self.empresa_id and
            self.cuenta_bancaria.empresa_id !=
            self.empresa_id
        ):

            raise ValidationError({

                'cuenta_bancaria':
                    'La cuenta bancaria debe pertenecer a la misma empresa que la tarjeta.'

            })


    def __str__(self):

        return (
            f"{self.nombre} - "
            f"{self.get_tipo_tarjeta_display()}"
        )

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

# =========================================
# USUARIOS / ACCESO A ORDENACLICK
# =========================================

class PerfilUsuario(models.Model):
    """
    Guarda los datos personales y el estado de acceso comercial de un usuario.

    El usuario de Django conserva la autenticación. Este modelo agrega los
    datos propios de OrdenaClick y permite que, más adelante, el dueño de la
    plataforma habilite, bloquee o limite el acceso sin mezclar esa decisión
    con los permisos que el usuario tenga dentro de cada empresa.
    """

    ESTADOS_ACCESO = [
        ("pendiente", "Pendiente"),
        ("demo", "Demo"),
        ("activo", "Activo"),
        ("bloqueado", "Bloqueado"),
    ]

    user = models.OneToOneField(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="perfil_ordenaclick"
    )

    nombre = models.CharField(
        max_length=100
    )

    apellido = models.CharField(
        max_length=100
    )

    telefono_personal = models.CharField(
        max_length=30,
        blank=True
    )

    telefono_laboral = models.CharField(
        max_length=30,
        blank=True
    )

    direccion_laboral = models.CharField(
        max_length=255,
        blank=True
    )

    estado_acceso = models.CharField(
        max_length=20,
        choices=ESTADOS_ACCESO,
        default="demo"
    )

    creado = models.DateTimeField(
        auto_now_add=True
    )

    actualizado = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        """Devuelve el nombre visible del usuario."""
        nombre_completo = f"{self.nombre} {self.apellido}".strip()
        return nombre_completo or self.user.username
