from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

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
    
    def get_role_display(self):
        """Método seguro para obtener el nombre del rol"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def get_role_request_display(self):
        """Método seguro para obtener el nombre del rol solicitado"""
        return dict(self.ROLE_CHOICES).get(self.role_request, self.role_request)


class Case(models.Model):
    
    # Opciones de estado del caso
    CASE_STATUS = [
        ('registrado', 'Registrado'),
        ('en_tramite', 'En trámite'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]
    
    # Opciones para los bloques
    BLOCK_CHOICES = [
        ('bloque_15', 'BLOQUE 15'),
        ('bloque_16', 'BLOQUE 16'),
        ('bloque_17', 'BLOQUE 17'),
        ('bloque_22p', 'BLOQUE 22 P'),
        ('bloque_23p', 'BLOQUE 23 P'),
        ('bloque_24p', 'BLOQUE 24 P'),
        ('bloque_25p', 'BLOQUE 25 P'),
        ('bloque_18', 'BLOQUE 18'),
        ('bloque_19', 'BLOQUE 19'),
        ('bloque_20', 'BLOQUE 20'),
        ('bloque_21', 'BLOQUE 21'),
        ('otro', 'OTRO'),
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
    
    # Opciones de método de resolución
    RESOLUTION_METHOD_CHOICES = [
        ('conciliacion', 'Conciliación'),
        ('mediacion', 'Mediación'),
        ('equidad', 'Resolución en equidad'),
        ('otro', 'Otro'),
    ]

    # Campo principal de estado (único, sin duplicados)
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=CASE_STATUS,
        default='registrado'
    )
    
    # ✅ CORRECCIÓN CRÍTICA: Aumentar longitud para almacenar múltiples bloques
    location_blocks = models.CharField(
        "Bloque(s) donde ocurre el conflicto", 
        max_length=500,  # ✅ Aumentado de 200 a 500
        blank=True,
        null=True
    )
    other_location_block = models.CharField(
        "Otro bloque", 
        max_length=100,
        blank=True,
        null=True
    )
    
    # ✅ CORRECCIÓN CRÍTICA: Aumentar longitud para almacenar múltiples métodos
    resolution_method = models.CharField(
        "Medio(s) de resolución", 
        max_length=500,  # ✅ Aumentado para múltiples métodos
        blank=True,
        null=True
    )
    other_resolution_method = models.CharField(
        "Otro medio de resolución", 
        max_length=100,
        blank=True,
        null=True
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
        default='vecinal'
    )
    other_conflict_type = models.CharField("Otro tipo de conflicto", max_length=100, blank=True, null=True)
    estimated_value = models.DecimalField("Valor aproximado (patrimonial)", max_digits=12, decimal_places=2, blank=True, null=True)

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
        ordering = ['-date_registered']
    
    def get_status_display(self):
        """Método seguro para obtener el nombre del estado"""
        return dict(self.CASE_STATUS).get(self.status, self.status)
    
    def get_conflict_type_display(self):
        """Método seguro para obtener el nombre del tipo de conflicto"""
        return dict(self.CONFLICT_TYPE_CHOICES).get(self.conflict_type, self.conflict_type)
    
    def get_location_blocks_list(self):
        """Convierte location_blocks de cadena a lista"""
        if not self.location_blocks:
            return []
        return [block.strip() for block in self.location_blocks.split(',') if block.strip()]
    
    def get_location_blocks_display(self):
        """Convierte los códigos de bloques a nombres legibles"""
        blocks = self.get_location_blocks_list()
        return [dict(self.BLOCK_CHOICES).get(block, block) for block in blocks]
    
    def get_resolution_method_list(self):
        """Convierte resolution_method de cadena a lista"""
        if not self.resolution_method:
            return []
        return [method.strip() for method in self.resolution_method.split(',') if method.strip()]
    
    def get_resolution_method_display(self):
        """Convierte los códigos de métodos a nombres legibles"""
        methods = self.get_resolution_method_list()
        return [dict(self.RESOLUTION_METHOD_CHOICES).get(method, method) for method in methods]

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
        performed_by=instance.judge,
        details=f"El caso {instance.case_number} fue eliminado."
    )