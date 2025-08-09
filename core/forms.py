from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import UserProfile, Case, PlatformSettings


class PlatformSettingsForm(forms.ModelForm):
    class Meta:
        model = PlatformSettings
        fields = ['logo', 'header_image', 'footer_text', 'primary_color', 'secondary_color']
        widgets = {
            'footer_text': forms.Textarea(attrs={'rows': 3}),
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
        }
        labels = {
            'logo': 'Logo del sistema',
            'header_image': 'Imagen de encabezado',
            'footer_text': 'Texto del pie de página',
            'primary_color': 'Color principal',
            'secondary_color': 'Color secundario',
        }


class UserRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label="Nombres completos",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    id_number = forms.CharField(
        label="Cédula",
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Solo números. Ej: 1234567890"
    )
    date_of_birth = forms.DateField(
        label="Fecha de nacimiento",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    phone = forms.CharField(
        label="Teléfono (opcional)",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        label="Dirección (opcional)",
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )
    role_request = forms.ChoiceField(
        label="Rol a solicitar",
        choices=[('juez', 'Juez de Paz'), ('admin', 'Administrador')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Mínimo 8 caracteres."
    )
    confirm_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    consentimiento_1 = forms.BooleanField(
        label="Declaro que la información proporcionada es verdadera y exacta.",
        required=True
    )
    consentimiento_2 = forms.BooleanField(
        label="Acepto que mi registro será revisado y aprobado por un administrador antes de acceder al sistema.",
        required=True
    )

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if not id_number.isdigit():
            raise ValidationError("La cédula debe contener solo números.")
        if UserProfile.objects.filter(id_number=id_number).exists():
            raise ValidationError("Ya existe un usuario con esta cédula.")
        return id_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        user_profile = UserProfile.objects.create(
            user=user,
            full_name=self.cleaned_data['full_name'],
            last_name=self.cleaned_data['last_name'],
            id_number=self.cleaned_data['id_number'],
            date_of_birth=self.cleaned_data['date_of_birth'],
            phone=self.cleaned_data['phone'],
            address=self.cleaned_data['address'],
            role_request=self.cleaned_data['role_request'],
            approved_by_admin=False
        )
        return user


class CaseForm(forms.ModelForm):
    CONFLICT_TYPE_CHOICES = [
        ('vecinal', 'Vecinal'),
        ('individual', 'Individual'),
        ('comunitario', 'Comunitario'),
        ('contravencion', 'Contravención sin privación de libertad'),
        ('patrimonial', 'Obligaciones patrimoniales hasta cinco salarios básicos'),
        ('otro', 'Otro'),
    ]

    RESOLUTION_METHOD_CHOICES = [
        ('conciliacion', 'Conciliación'),
        ('mediacion', 'Mediación'),
        ('equidad', 'Resolución en equidad'),
        ('otro', 'Otro'),
    ]

    conflict_type = forms.ChoiceField(
        label="Tipo de conflicto",
        choices=CONFLICT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    resolution_method = forms.MultipleChoiceField(
        label="Medio solicitado (opcional)",
        choices=RESOLUTION_METHOD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    other_resolution_method = forms.CharField(
        label="Otro medio de resolución",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    other_conflict_type = forms.CharField(
        label="Especifique otro tipo de conflicto",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    consentimiento_1 = forms.BooleanField(
        label="Confirmo que la información proporcionada es verdadera.",
        required=True
    )
    consentimiento_2 = forms.BooleanField(
        label="Autorizo que mi caso sea gestionado conforme a la Ley y la normativa aplicable.",
        required=True
    )

    class Meta:
        model = Case
        fields = [
            'applicant_name', 'applicant_id', 'applicant_phone', 'applicant_email',
            'involved_name', 'involved_id',
            'conflict_description', 'location',
            'estimated_value',
            'notes'
        ]
        widgets = {
            'conflict_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'applicant_name': 'Nombre del solicitante',
            'applicant_id': 'Cédula del solicitante',
            'applicant_phone': 'Teléfono del solicitante',
            'applicant_email': 'Correo del solicitante',
            'involved_name': 'Nombre del involucrado',
            'involved_id': 'Cédula del involucrado',
            'conflict_description': 'Descripción del conflicto',
            'location': 'Lugar donde ocurre el conflicto',
            'estimated_value': 'Valor aproximado (si aplica, en caso patrimonial)',
            'notes': 'Observaciones adicionales'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar checkboxes de resolución
        if self.instance.pk and self.instance.resolution_method:
            self.fields['resolution_method'].initial = [
                method.strip() for method in self.instance.resolution_method.split(',') if method.strip()
            ]
        # ✅ Ocultar consentimientos si es edición (caso ya existe)
        if self.instance.pk:
            self.fields['consentimiento_1'].widget = forms.HiddenInput()
            self.fields['consentimiento_2'].widget = forms.HiddenInput()
            self.fields['consentimiento_1'].initial = True
            self.fields['consentimiento_2'].initial = True
            self.fields['consentimiento_1'].required = False
            self.fields['consentimiento_2'].required = False

    def clean(self):
        cleaned_data = super().clean()
        resolution_method = cleaned_data.get('resolution_method')
        other_resolution_method = cleaned_data.get('other_resolution_method')
        conflict_type = cleaned_data.get('conflict_type')
        other_conflict_type = cleaned_data.get('other_conflict_type')

        if resolution_method and 'otro' in resolution_method and not other_resolution_method:
            self.add_error('other_resolution_method', 'Debe especificar el otro medio de resolución.')

        if conflict_type == 'otro' and not other_conflict_type:
            self.add_error('other_conflict_type', 'Debe especificar el otro tipo de conflicto.')

        return cleaned_data