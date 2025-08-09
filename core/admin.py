from django.contrib import admin
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import AuditLog, UserProfile, Case, PlatformSettings


# ----------------------------------------------------------------------------------
# ✅ ADMINISTRACIÓN DE USUARIOS (UserProfile)
# - Mostrar, filtrar y aprobar Jueces de Paz
# ----------------------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'last_name',
        'id_number',
        'role_request',
        'approved_by_admin',
        'role'
    )
    list_filter = ('role_request', 'approved_by_admin', 'role')
    search_fields = ('full_name', 'last_name', 'id_number')
    list_editable = ('approved_by_admin', 'role')
    readonly_fields = ('id_number',)

    fieldsets = (
        ('Información Personal', {
            'fields': ('full_name', 'last_name', 'id_number', 'date_of_birth', 'phone', 'address')
        }),
        ('Autenticación', {
            'fields': ('user', 'username', 'email')
        }),
        ('Rol y Estado', {
            'fields': ('role_request', 'approved_by_admin', 'role')
        }),
    )

    def username(self, obj):
        return obj.user.username
    username.short_description = 'Nombre de usuario'

    def email(self, obj):
        return obj.user.email
    email.short_description = 'Correo electrónico'

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.approved_by_admin:
            return self.readonly_fields + ('role',)
        return self.readonly_fields


# ----------------------------------------------------------------------------------
# ✅ ADMINISTRACIÓN DE CASOS (Case)
# - Gestión completa de casos comunitarios
# - Solo lectura en campos automáticos
# ----------------------------------------------------------------------------------
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'case_number',
        'applicant_name',
        'involved_name',
        'status',
        'judge',
        'date_registered',
        'extension_granted'
    )
    list_filter = ('status', 'conflict_type', 'date_registered', 'judge', 'extension_granted')
    search_fields = ('case_number', 'applicant_name', 'involved_name', 'applicant_id', 'involved_id')
    readonly_fields = ('case_number', 'date_registered')
    date_hierarchy = 'date_registered'
    ordering = ('-date_registered',)

    fieldsets = (
        ('Número y Fecha', {
            'fields': ('case_number', 'date_registered')
        }),
        ('Solicitante', {
            'fields': ('applicant_name', 'applicant_id', 'applicant_phone', 'applicant_email')
        }),
        ('Involucrado', {
            'fields': ('involved_name', 'involved_id')
        }),
        ('Detalles del Conflicto', {
            'fields': ('conflict_description', 'location', 'conflict_type', 'other_conflict_type', 'estimated_value')
        }),
        ('Resolución', {
            'fields': ('resolution_method', 'other_resolution_method', 'notes')
        }),
        ('Gestión', {
            'fields': ('status', 'judge', 'extension_granted')
        }),
    )


# ----------------------------------------------------------------------------------
# ✅ ADMINISTRACIÓN DE CONFIGURACIÓN DE PLATAFORMA (PlatformSettings)
# - Solo un registro permitido
# - Vista previa de imágenes
# - Evita múltiples instancias
# - ✅ Corregido: uso de format_html (seguro en Django 3.0+)
# ----------------------------------------------------------------------------------
@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ('primary_color', 'secondary_color', 'logo_preview', 'header_preview')
    readonly_fields = ('logo_preview', 'header_preview')

    fieldsets = (
        ('Personalización Visual', {
            'fields': ('logo', 'logo_preview', 'header_image', 'header_preview'),
            'description': 'Sube el logo y la imagen de encabezado de la plataforma.'
        }),
        ('Colores', {
            'fields': ('primary_color', 'secondary_color'),
            'description': 'Define los colores principales del sistema.'
        }),
        ('Texto', {
            'fields': ('footer_text',),
            'description': 'Texto que aparecerá en el pie de página.'
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.logo.url)
        return "No hay logo"
    logo_preview.short_description = "Vista Previa del Logo"

    def header_preview(self, obj):
        if obj.header_image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 400px;" />', obj.header_image.url)
        return "No hay imagen de encabezado"
    header_preview.short_description = "Vista Previa del Encabezado"

    def has_add_permission(self, request):
        # Evita crear más de un registro
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Evita eliminar el registro único
        return False

    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('create/', self.create_singleton, name='platformsettings_create'),
        ]
        return custom_urls + urls

    def create_singleton(self, request):
        obj, created = PlatformSettings.objects.get_or_create(
            pk=1,
            defaults={
                'primary_color': '#0057B7',
                'secondary_color': '#FFD700'
            }
        )
        return redirect('admin:core_platformsettings_change', obj.pk)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'case_number', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp', 'performed_by')
    search_fields = ('case_number', 'performed_by__username', 'details')
    readonly_fields = ('action', 'case_number', 'performed_by', 'timestamp', 'details')
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False  # No se pueden crear manualmente
    
    
