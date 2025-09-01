from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Case, UserProfile, PlatformSettings
from .forms import PlatformSettingsForm, UserRegistrationForm, CaseForm
import csv
import json
from django.http import HttpResponse
from django.db.models import Count

from django.contrib.auth import logout

def logout_view(request):
    """
    Vista: Cerrar sesión
    Redirige a home después de cerrar sesión
    """
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('core:home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Tu solicitud ha sido enviada. '
                'El administrador revisará tu registro y te notificará por correo cuando sea aprobado.'
            )
            return redirect('core:register')
    else:
        form = UserRegistrationForm()
    settings = PlatformSettings.load()
    return render(request, 'core/register.html', {'form': form, 'settings': settings})


def login_view(request):
    # ✅ Limpiar mensajes previos (evita que aparezca "cerraste sesión" al iniciar)
    if request.method == 'GET':
        # Solo limpia al cargar el formulario, no durante POST
        storage = messages.get_messages(request)
        for _ in storage:
            pass  # Consumir y descartar mensajes antiguos

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            profile = getattr(user, 'profile', None)
            if profile and profile.role == 'admin':
                return redirect('core:admin_panel')
            elif profile and profile.role == 'juez':
                return redirect('core:judge_panel')
            else:
                return redirect('core:home')
        else:
            return render(request, 'core/login.html', {'error': 'Usuario o contraseña incorrectos'})
    else:
        return render(request, 'core/login.html')


def home(request):
    settings = PlatformSettings.load()
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'admin':
            return redirect('core:admin_panel')
        elif profile and profile.role == 'juez':
            return redirect('core:judge_panel')
    return render(request, 'core/home.html', {'settings': settings})


@login_required
def admin_panel(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    pending_users = UserProfile.objects.filter(approved_by_admin=False)
    cases = Case.objects.all().order_by('-date_registered')

    status_filter = request.GET.get('status')
    judge_filter = request.GET.get('judge')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status_filter:
        cases = cases.filter(status=status_filter)
    if judge_filter:
        cases = cases.filter(judge__username__icontains=judge_filter)
    if date_from:
        cases = cases.filter(date_registered__date__gte=date_from)
    if date_to:
        cases = cases.filter(date_registered__date__lte=date_to)

    query = request.GET.get('q')
    if query:
        cases = cases.filter(
            Q(case_number__icontains=query) |
            Q(applicant_id__icontains=query) |
            Q(involved_id__icontains=query)
        )

    total_cases = cases.count()
    cases_by_status = {}
    for status, label in Case.CASE_STATUS:
        count = cases.filter(status=status).count()
        cases_by_status[label] = count

    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de datos para gráficos
    # Datos para gráfico de casos por estado
    status_labels = []  # ✅ Etiquetas: "En trámite", "Resuelto", "Cerrado"
    status_values = []  # ✅ Valores: 5, 3, 2, etc.
    
    # ✅ Solo incluir estos estados en el gráfico
    relevant_statuses = ['en_tramite', 'resuelto', 'cerrado']
    for status, label in Case.CASE_STATUS:
        if status in relevant_statuses:
            count = cases.filter(status=status).count()
            status_labels.append(label)
            status_values.append(count)

    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de conflict_data
    # Datos para gráfico de tipos de conflicto
    conflict_data = (
        cases
        .values('conflict_type')
        .annotate(count=Count('conflict_type'))
        .order_by('-count')
    )
    conflict_labels = []
    conflict_values = []
    # ✅ Bucle corregido: for item in conflict_data (no conflict_)
    for item in conflict_data:
        label = dict(Case.CONFLICT_TYPE_CHOICES).get(item['conflict_type'], item['conflict_type'])
        conflict_labels.append(label)
        conflict_values.append(item['count'])
        
    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de block_data
    # Datos para gráfico de bloques
    block_data = (
        cases
        .values('location_blocks')
        .annotate(count=Count('location_blocks'))
        .order_by('-count')
    )
    block_labels = []
    block_values = []
    # ✅ Bucle corregido: for item in block_data (no block_)
    for item in block_data:
        # Procesar múltiples bloques
        if item['location_blocks']:
            blocks = [b.strip() for b in item['location_blocks'].split(',') if b.strip()]
            for block in blocks:
                # Convertir el código del bloque a su nombre legible
                label = dict(Case.BLOCK_CHOICES).get(block, block)
                if label in block_labels:
                    idx = block_labels.index(label)
                    block_values[idx] += item['count']
                else:
                    block_labels.append(label)
                    block_values.append(item['count'])

    context = {
        'pending_users': pending_users,
        'cases': cases,
        'total_cases': total_cases,
        'cases_by_status': cases_by_status,
        'CASE_STATUS': Case.CASE_STATUS,
        'all_judges': User.objects.filter(profile__role='juez').distinct(),
        'filter_status': status_filter,
        'filter_judge': judge_filter,
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'query': query,
        'settings': settings,
        # ✅ DATOS CORREGIDOS PARA GRÁFICOS
        'status_labels': json.dumps(status_labels),
        'status_values': json.dumps(status_values),
        'conflict_labels': json.dumps(conflict_labels),
        'conflict_values': json.dumps(conflict_values),
        'block_labels': json.dumps(block_labels),
        'block_values': json.dumps(block_values),
    }
    return render(request, 'core/admin_panel.html', context)


@login_required
def judge_panel(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'juez':
        return redirect('core:admin_panel')

    settings = PlatformSettings.load()
    cases = Case.objects.filter(judge=request.user).order_by('-date_registered')

    query = request.GET.get('q')
    if query:
        cases = cases.filter(
            Q(case_number__icontains=query) |
            Q(applicant_id__icontains=query)
        )

    return render(request, 'core/judge_panel.html', {'cases': cases, 'settings': settings})


@login_required
def register_case(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'juez':
        messages.error(request, "No tienes permiso para registrar casos.")
        return redirect('core:admin_panel')

    settings = PlatformSettings.load()
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.judge = request.user
            now = timezone.now()
            year = now.year
            month = now.month
            count = Case.objects.filter(
                date_registered__year=year,
                date_registered__month=month
            ).count() + 1
            case.case_number = f"JC-{year}-{month:02d}-{count:04d}"
            case.save()

            # ✅ CORRECCIÓN CRÍTICA: Manejar resolution_methods como lista vacía si es None
            resolution_methods = form.cleaned_data.get('resolution_method') or []
            if resolution_methods:
                case.resolution_method = ', '.join(resolution_methods)
                if 'otro' in resolution_methods:
                    case.other_resolution_method = form.cleaned_data.get('other_resolution_method')
                case.save()

            if case.conflict_type == 'otro':
                case.other_conflict_type = form.cleaned_data.get('other_conflict_type')
                case.save()
                
            # ✅ CORRECCIÓN CRÍTICA: Manejar location_blocks como lista vacía si es None
            location_blocks = form.cleaned_data.get('location_blocks') or []
            if location_blocks:
                case.location_blocks = ', '.join(location_blocks)
                if 'otro' in location_blocks:
                    case.other_location_block = form.cleaned_data.get('other_location_block')
                case.save()

            messages.success(request, f'Caso registrado con éxito. Número de caso: {case.case_number}')
            return redirect('core:judge_panel')
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = CaseForm()
        
    settings = PlatformSettings.load()

    return render(request, 'core/register_case.html', {'form': form, 'settings': settings})


@login_required
def case_detail(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'juez':
        messages.error(request, "No tienes permiso para ver este caso.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id, judge=request.user)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe o no tienes permiso para verlo.")
        return redirect('core:judge_panel')

    days_elapsed = (timezone.now() - case.date_registered).days
    max_days = 15
    if case.extension_granted:
        max_days = 30

    progress = min(int((days_elapsed / max_days) * 100), 100) if max_days > 0 else 0

    if days_elapsed >= max_days:
        deadline_status = "Vencido"
        deadline_class = "danger"
    elif days_elapsed >= max_days - 5:
        deadline_status = "Urgente"
        deadline_class = "warning"
    else:
        deadline_status = "En tiempo"
        deadline_class = "success"

    return render(request, 'core/case_detail.html', {
        'case': case,
        'days_elapsed': days_elapsed,
        'max_days': max_days,
        'progress': progress,
        'deadline_status': deadline_status,
        'deadline_class': deadline_class,
        'settings': settings,
    })


@login_required
def update_case_status(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'juez':
        messages.error(request, "No tienes permiso para actualizar este caso.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id, judge=request.user)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe o no tienes permiso para actualizarlo.")
        return redirect('core:judge_panel')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        # ✅ Solo permitir ciertos estados para los jueces
        allowed_statuses = ['en_tramite', 'resuelto', 'cerrado']
        if new_status in allowed_statuses:
            case.status = new_status
            case.save()
            messages.success(request, f"Estado del caso actualizado a: {case.get_status_display()}")
        else:
            messages.error(request, "Estado no válido para un Juez de Paz.")
        return redirect('core:case_detail', case_id=case.id)

    return redirect('core:case_detail', case_id=case.id)


@login_required
def request_extension(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'juez':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id, judge=request.user)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe o no tienes permiso para solicitar prórroga.")
        return redirect('core:judge_panel')

    if case.extension_granted:
        messages.warning(request, "Ya se ha concedido una prórroga para este caso.")
    else:
        case.extension_granted = True
        case.save()
        messages.success(request, "Prórroga de 15 días concedida. El plazo ahora es de 30 días.")
    
    return redirect('core:case_detail', case_id=case.id)


@login_required
def approve_user(request, user_profile_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    try:
        user_profile = get_object_or_404(UserProfile, id=user_profile_id)
        user_profile.approved_by_admin = True
        user_profile.role = user_profile.role_request
        user_profile.save()

        messages.success(
            request,
            f"Usuario '{user_profile.full_name} {user_profile.last_name}' aprobado como {user_profile.get_role_display()}."
        )
    except Exception as e:
        messages.error(request, f"Error al aprobar usuario: {str(e)}")
    
    return redirect('core:admin_panel')


@login_required
def reject_user(request, user_profile_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    try:
        user_profile = get_object_or_404(UserProfile, id=user_profile_id)
        user = user_profile.user
        user_profile.delete()
        user.delete()

        messages.success(request, "Usuario rechazado y eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al rechazar usuario: {str(e)}")
    
    return redirect('core:admin_panel')


@login_required
def admin_case_detail(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()
    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe.")
        return redirect('core:admin_panel')

    days_elapsed = (timezone.now() - case.date_registered).days
    max_days = 15
    if case.extension_granted:
        max_days = 30

    progress = min(int((days_elapsed / max_days) * 100), 100) if max_days > 0 else 0

    if days_elapsed >= max_days:
        deadline_status = "Vencido"
        deadline_class = "danger"
    elif days_elapsed >= max_days - 5:
        deadline_status = "Urgente"
        deadline_class = "warning"
    else:
        deadline_status = "En tiempo"
        deadline_class = "success"

    return render(request, 'core/admin_case_detail.html', {
        'case': case,
        'days_elapsed': days_elapsed,
        'max_days': max_days,
        'progress': progress,
        'deadline_status': deadline_status,
        'deadline_class': deadline_class,
        'settings': settings,
    })
# ----------------------------------------------------------------------------------
# ✅ EDITAR CASO (Admin)
# - Solo accesible para el Admin
# - Permite modificar todos los campos del caso
# ----------------------------------------------------------------------------------
@login_required
def edit_case(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe.")
        return redirect('core:admin_panel')

    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            # Guardamos el caso, pero sin guardar aún en la base de datos
            case = form.save(commit=False)

            # Actualizamos resolution_method (si aplica)
            resolution_methods = form.cleaned_data.get('resolution_method') or []
            if resolution_methods:
                case.resolution_method = ', '.join(resolution_methods)
                if 'otro' in resolution_methods:
                    case.other_resolution_method = form.cleaned_data.get('other_resolution_method')

            # Actualizamos other_conflict_type si el tipo es "otro"
            if case.conflict_type == 'otro':
                case.other_conflict_type = form.cleaned_data.get('other_conflict_type')
                
            # ✅ Actualizamos location_blocks
            location_blocks = form.cleaned_data.get('location_blocks') or []
            if location_blocks:
                case.location_blocks = ', '.join(location_blocks)
                if 'otro' in location_blocks:
                    case.other_location_block = form.cleaned_data.get('other_location_block')

            # Guardamos el caso en la base de datos
            case.save()

            # Mensaje de éxito y redirección
            messages.success(request, f"Caso {case.case_number} actualizado correctamente.")
            return redirect('core:admin_case_detail', case_id=case.id)
        else:
            # Mostrar errores en consola (opcional, para depurar)
            print("Errores del formulario:", form.errors)
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        # Si es GET, mostramos el formulario con los datos actuales
        form = CaseForm(instance=case)
        # Inicializamos los checkboxes de resolución
        if case.resolution_method:
            form.fields['resolution_method'].initial = [
                method.strip() for method in case.resolution_method.split(',') if method.strip()
            ]
        # ✅ Inicializamos los checkboxes de bloques
        if case.location_blocks:
            form.fields['location_blocks'].initial = [
                block.strip() for block in case.location_blocks.split(',') if block.strip()
            ]

    # Cargamos la configuración de la plataforma
    settings = PlatformSettings.load()

    # Renderizamos la plantilla
    return render(request, 'core/edit_case.html', {
        'form': form,
        'case': case,
        'settings': settings,
    })
# ----------------------------------------------------------------------------------
# ✅ ELIMINAR CASO (Admin)
# - Solo accesible para el Admin
# - Pide confirmación antes de eliminar
# ----------------------------------------------------------------------------------
@login_required
def delete_case(request, case_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    # ✅ CORRECCIÓN CRÍTICA: Manejo seguro de get_object_or_404
    try:
        case = get_object_or_404(Case, id=case_id)
    except Case.DoesNotExist:
        messages.error(request, "El caso no existe.")
        return redirect('core:admin_panel')

    if request.method == 'POST':
        case_number = case.case_number
        case.delete()
        messages.success(request, f"Caso {case_number} eliminado correctamente.")
        return redirect('core:admin_panel')

    return render(request, 'core/delete_case.html', {
        'case': case,
        'settings': PlatformSettings.load()
    })
@login_required
def download_cases_csv(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        return redirect('core:home')

    settings = PlatformSettings.load()
    cases = Case.objects.all().order_by('-date_registered')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_casos_comunitarios.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Número de Caso', 'Fecha de Registro', 'Solicitante', 'Cédula Solicitante',
        'Involucrado', 'Cédula Involucrado', 'Lugar', 'Tipo de Conflicto',
        'Bloque(s)', 'Otro bloque', 'Valor Estimado', 'Estado', 'Juez Asignado', 
        'Prórroga', 'Observaciones'
    ])

    for case in cases:
        writer.writerow([
            case.case_number,
            case.date_registered.strftime('%d/%m/%Y %H:%M'),
            case.applicant_name,
            case.applicant_id,
            case.involved_name,
            case.involved_id,
            case.location,
            case.get_conflict_type_display(),
            case.location_blocks,
            case.other_location_block or '',
            case.estimated_value or '',
            case.get_status_display(),
            case.judge.username,
            'Sí' if case.extension_granted else 'No',
            case.notes or ''
        ])

    return response

# ----------------------------------------------------------------------------------
# ✅ VISTA: Personalización de la Plataforma
# - Solo accesible para el Admin
# - Permite subir logo, cambiar colores, etc.
# ----------------------------------------------------------------------------------
@login_required
def platform_settings(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'admin':
        messages.error(request, "Acceso denegado.")
        return redirect('core:home')

    settings = PlatformSettings.load()

    if request.method == 'POST':
        form = PlatformSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración actualizada correctamente.")
            return redirect('core:admin_panel')
    else:
        form = PlatformSettingsForm(instance=settings)

    return render(request, 'core/platform_settings.html', {'form': form})


from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def recover_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generar token y UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            # Crear enlace de recuperación
            reset_url = request.build_absolute_uri(
                reverse('core:reset_password', kwargs={'uidb64': uid, 'token': token})
            )
            # Enviar correo
            send_mail(
                subject="Recuperación de contraseña",
                message=f"Haz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "Se ha enviado un enlace de recuperación a tu correo.")
            return redirect('core:login')
        except User.DoesNotExist:
            messages.error(request, "No existe un usuario con ese correo.")
    return render(request, 'core/recover_password.html')


from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import login

def reset_password(request, uidb64, token):
    try:
        # Decodificar UID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password != confirm_password:
                messages.error(request, "Las contraseñas no coinciden.")
            else:
                user.set_password(password)
                user.save()
                messages.success(request, "Contraseña actualizada con éxito.")
                login(request, user)
                return redirect('core:home')
        return render(request, 'core/reset_password.html')
    else:
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect('core:login')