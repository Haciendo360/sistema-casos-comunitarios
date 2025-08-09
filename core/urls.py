from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('judge-panel/', views.judge_panel, name='judge_panel'),
    path('register-case/', views.register_case, name='register_case'),
    path('case/<int:case_id>/', views.case_detail, name='case_detail'),
    path('update-case-status/<int:case_id>/', views.update_case_status, name='update_case_status'),
    path('request-extension/<int:case_id>/', views.request_extension, name='request_extension'),
    path('approve-user/<int:user_profile_id>/', views.approve_user, name='approve_user'),
    path('reject-user/<int:user_profile_id>/', views.reject_user, name='reject_user'),
    path('admin-case-detail/<int:case_id>/', views.admin_case_detail, name='admin_case_detail'),
    path('download-cases-csv/', views.download_cases_csv, name='download_cases_csv'),
    # ✅ Vista de personalización
    path('platform-settings/', views.platform_settings, name='platform_settings'),
    path('recover-password/', views.recover_password, name='recover_password'),
path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
path('logout/', views.logout_view, name='logout'),

path('edit-case/<int:case_id>/', views.edit_case, name='edit_case'),
path('delete-case/<int:case_id>/', views.delete_case, name='delete_case'),
]