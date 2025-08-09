from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField("Nombres completos", max_length=100, blank=False)
    last_name = models.CharField("Apellidos", max_length=100, blank=False)
    id_number = models.CharField("Cédula", max_length=20, unique=True, blank=False)
    date_of_birth = models.DateField("Fecha de nacimiento", blank=False)
    phone = models.CharField("Teléfono", max_length=20, blank=True, null=True)
    address = models.TextField("Dirección", blank=True, null=True)
    EMAIL_FIELD = 'user__email'

    ROLE_CHOICES = [
        ('juez', 'Juez de Paz'),
        ('admin', 'Administrador'),
    ]
    role_request = models.CharField("Rol a solicitar", max_length=10, choices=ROLE_CHOICES, blank=False)
    approved_by_admin = models.BooleanField("Aprobado por Admin", default=False)
    role = models.CharField("Rol asignado", max_length=10, choices=ROLE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} {self.last_name}"

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"


class Case(models.Model):
    
    # Opciones de estado del caso
    CASE_STATUS = [
        ('registrado', 'Registrado'),
        ('en_tramite', 'En trámite'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
        ('prorroga', 'Prórroga'),
    ]

    # Opciones de tipo de conflicto
    CONFLICT_TYPE_CHOICES = [
        ('vecinal', 'Vecinal'),
        ('individual', 'Individual'),
        ('comunitario', 'Comunitario'),
        ('contravencion', 'Contravención sin privación de libertad'),
        ('patrimonial', 'Obligaciones patrimoniales hasta cinco salarios básicos'),
        ('otro', 'Otro'),
    ]

    # Campo principal de estado (único, sin duplicados)
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=CASE_STATUS,
        default='registrado'
    )

    # Número de caso y fecha
    case_number = models.CharField("Número de caso", max_length=20, unique=True, editable=False)
    date_registered = models.DateTimeField("Fecha de registro", auto_now_add=True)

    # Solicitante
    applicant_name = models.CharField("Nombre del solicitante", max_length=100, blank=False)
    applicant_id = models.CharField("Cédula del solicitante", max_length=20, blank=False)
    applicant_phone = models.CharField("Teléfono del solicitante", max_length=20, blank=True, null=True)
    applicant_email = models.EmailField("Correo del solicitante", blank=True, null=True)

    # Involucrado
    involved_name = models.CharField("Nombre del involucrado", max_length=100, blank=False)
    involved_id = models.CharField("Cédula del involucrado", max_length=20, blank=True, null=True)

    # Detalles del caso
    conflict_description = models.TextField("Descripción del conflicto", blank=False)
    location = models.CharField("Lugar del conflicto", max_length=200, blank=False)
    conflict_type = models.CharField(
    "Tipo de conflicto", 
    max_length=50, 
    choices=CONFLICT_TYPE_CHOICES, 
    blank=False,
    default='vecinal'  # ✅ Asegura que siempre tenga un valor
)
    other_conflict_type = models.CharField("Otro tipo de conflicto", max_length=100, blank=True, null=True)
    estimated_value = models.DecimalField("Valor aproximado (patrimonial)", max_digits=12, decimal_places=2, blank=True, null=True)

    # Medio de resolución
    resolution_method = models.CharField("Medio de resolución", max_length=200, blank=True, null=True)
    other_resolution_method = models.CharField("Otro medio", max_length=100, blank=True, null=True)

    # Observaciones
    notes = models.TextField("Observaciones adicionales", blank=True, null=True)

    # Juez asignado y prórroga
    judge = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Juez asignado",
        related_name='cases_judge'
    )
    extension_granted = models.BooleanField("Prórroga concedida", default=False)

    def __str__(self):
        return f"{self.case_number} - {self.applicant_name}"

    class Meta:
        verbose_name = "Caso Comunitario"
        verbose_name_plural = "Casos Comunitarios"


# ----------------------------------------------------------------------------------
# ✅ MODELO: Auditoría de Acciones
# - Registra quién hizo qué y cuándo
# - No afecta el resto del sistema
# ----------------------------------------------------------------------------------
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Creado'),
        ('UPDATED', 'Actualizado'),
        ('DELETED', 'Eliminado'),
    ]

    action = models.CharField("Acción", max_length=10, choices=ACTION_CHOICES)
    case_number = models.CharField("Número de Caso", max_length=20, blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Realizado por")
    timestamp = models.DateTimeField("Fecha y hora", auto_now_add=True)
    details = models.TextField("Detalles", blank=True, null=True)

    def __str__(self):
        user_name = self.performed_by.get_full_name() or self.performed_by.username if self.performed_by else "Sistema"
        return f"{self.get_action_display()} - {self.case_number or 'N/A'} por {user_name}"

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-timestamp']


# ----------------------------------------------------------------------------------
# ✅ CONFIGURACIÓN DE LA PLATAFORMA (Personalización)
# - Logo, encabezado, colores, texto del pie
# - Único registro en la base de datos
# ----------------------------------------------------------------------------------
class PlatformSettings(models.Model):
    logo = models.ImageField(
        "Logo",
        upload_to='settings/',
        blank=True,
        null=True
    )
    header_image = models.ImageField(
        "Imagen de encabezado",
        upload_to='settings/',
        blank=True,
        null=True
    )
    footer_text = models.TextField(
        "Texto del pie de página",
        blank=True,
        null=True
    )
    primary_color = models.CharField(
        "Color primario",
        max_length=7,
        default="#0057B7"
    )
    secondary_color = models.CharField(
        "Color secundario",
        max_length=7,
        default="#FFD700"
    )

    def __str__(self):
        return "Configuración de la Plataforma"

    class Meta:
        verbose_name = "Configuración de Plataforma"
        verbose_name_plural = "Configuración de Plataforma"

    def save(self, *args, **kwargs):
        """
        Asegura que solo exista un registro de configuración
        """
        if not self.pk and PlatformSettings.objects.exists():
            # Evita crear más de un registro
            return
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """
        Obtiene la instancia única de configuración
        """
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'primary_color': '#0057B7',
                'secondary_color': '#FFD700'
            }   
            
        )
           
        return obj
    
    # ----------------------------------------------------------------------------------
# ✅ SEÑALES: Registrar acciones automáticamente
# - Cada vez que se crea, edita o elimina un caso
# ----------------------------------------------------------------------------------
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Case)
def log_case_creation_or_update(sender, instance, created, **kwargs):
    if created:
        action = 'CREATED'
        details = f"El caso {instance.case_number} fue creado."
    else:
        action = 'UPDATED'
        details = f"El caso {instance.case_number} fue actualizado."
    
    AuditLog.objects.create(
        action=action,
        case_number=instance.case_number,
        performed_by=instance.judge,
        details=details
    )

@receiver(post_delete, sender=Case)
def log_case_deletion(sender, instance, **kwargs):
    AuditLog.objects.create(
        action='DELETED',
        case_number=instance.case_number,
        performed_by=getattr(instance.judge, 'profile', None).user if hasattr(instance.judge, 'profile') else None,
        details=f"El caso {instance.case_number} fue eliminado."
    )
    
# ----------------------------------------------------------------------------------
# ✅ MODELO: Auditoría de Acciones
# - Registra quién creó, editó o eliminó un caso
# - No afecta el resto del sistema
# ----------------------------------------------------------------------------------
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATED', 'Creado'),
        ('UPDATED', 'Actualizado'),
        ('DELETED', 'Eliminado'),
    ]

    action = models.CharField("Acción", max_length=10, choices=ACTION_CHOICES)
    case_number = models.CharField("Número de Caso", max_length=20, blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Realizado por")
    timestamp = models.DateTimeField("Fecha y hora", auto_now_add=True)
    details = models.TextField("Detalles", blank=True, null=True)

    def __str__(self):
        user_name = self.performed_by.get_full_name() or self.performed_by.username if self.performed_by else "Sistema"
        return f"{self.get_action_display()} - {self.case_number or 'N/A'} por {user_name}"

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-timestamp']