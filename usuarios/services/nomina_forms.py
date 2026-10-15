"""Formularios seguros de nómina; los IDs externos se limitan por Empresa."""
import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.utils import timezone
from usuarios.models import Empleado, CentroOperativo, RecursoOperativo, Banco


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = (
            'cuil', 'nombre_apellido', 'fecha_nacimiento', 'legajo', 'direccion',
            'telefono_personal', 'mail_personal', 'mail_laboral', 'telefono_laboral',
            'fecha_vencimiento_licencia', 'emergencia_nombre', 'emergencia_telefono',
            'fecha_ingreso', 'centro_operativo', 'vehiculo', 'cbu', 'banco',
            'tipo_contratacion',
        )
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_vencimiento_licencia': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, empresa, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        # Modelo: 11 dígitos; pantalla: 13 caracteres con guiones, como CUIT.
        self.fields['cuil'].max_length = 13
        # ModelForm conservaba MaxLengthValidator(11) aunque cambiara
        # max_length a 13: ese validador corría antes de clean_cuil().
        # Los guiones son presentación; clean_cuil() persiste 11 dígitos.
        self.fields['cuil'].validators = [
            validador for validador in self.fields['cuil'].validators
            if not isinstance(validador, MaxLengthValidator)
        ] + [MaxLengthValidator(13)]
        self.fields['cuil'].widget.attrs.update({'maxlength': '13', 'inputmode': 'numeric', 'placeholder': '20-32390769-3'})
        self.fields['centro_operativo'].required = True
        self.fields['centro_operativo'].required = True
        self.fields['centro_operativo'].required = True
        self.fields['centro_operativo'].required = True
        self.fields['centro_operativo'].queryset = CentroOperativo.objects.filter(empresa=empresa, activo=True)
        self.fields['vehiculo'].queryset = RecursoOperativo.objects.filter(empresa=empresa, activo=True, tipo_recurso='Vehiculo')
        self.fields['banco'].queryset = Banco.objects.filter(empresa=empresa, activo=True)
        for name in ('centro_operativo', 'vehiculo', 'banco'):
            self.fields[name].empty_label = 'Seleccionar' if name == 'centro_operativo' else 'Sin asignar'
        for name in ('fecha_nacimiento', 'fecha_ingreso', 'fecha_vencimiento_licencia'):
            self.fields[name].input_formats = ['%Y-%m-%d']

    def clean_cuil(self):
        cuil = re.sub(r'[ -]', '', self.cleaned_data['cuil'])
        if not re.fullmatch(r'\d{11}', cuil):
            raise ValidationError('El CUIL debe tener exactamente 11 dígitos.')
        pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
        digito = (11 - sum(int(x) * p for x, p in zip(cuil[:10], pesos)) % 11) % 11
        if digito == 10 or int(cuil[-1]) != digito:
            raise ValidationError('El dígito verificador del CUIL no es válido.')
        if Empleado.objects.filter(empresa=self.empresa, cuil=cuil).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe un empleado con este CUIL en la Empresa, incluso si está inactivo.')
        return cuil

    def clean_legajo(self):
        value = (self.cleaned_data['legajo'] or '').strip().upper()
        if not value:
            raise ValidationError('Ingresá el legajo.')
        if Empleado.objects.filter(empresa=self.empresa, legajo__iexact=value).exclude(pk=self.instance.pk).exists():
            raise ValidationError('El legajo ya existe en esta Empresa, incluso si está inactivo.')
        return value

    def clean_cbu(self):
        value = re.sub(r'\s+', '', self.cleaned_data.get('cbu') or '')
        if value and not re.fullmatch(r'\d{22}', value):
            raise ValidationError('El CBU debe contener 22 dígitos.')
        return value

    def clean(self):
        data = super().clean()
        nacimiento, ingreso = data.get('fecha_nacimiento'), data.get('fecha_ingreso')
        if nacimiento and ingreso and ingreso < nacimiento:
            self.add_error('fecha_ingreso', 'No puede ser anterior al nacimiento.')
        return data
