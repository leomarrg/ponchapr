from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.pre_register, name='pre_register'),
    path('register/', views.front_desk_register, name='register'),
    path('api/checkin/', views.verify_checkin_qr_code, name='verify_checkin_qr_code'),
    path('api/checkout/', views.verify_checkout_qr_code, name='verify_checkout_qr_code'),
    path('qr-scan-checkin/', views.checkin_qr_code_verify, name='checkin_qr_code_verify'),
    path('qr-scan-checkout/', views.checkout_qr_code_verify, name='checkout_qr_code_verify'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('check-in/<int:attendee_id>/', views.check_in_attendee, name='check_in_attendee'),
    path('checkout/', views.checkout_form, name='checkout_form'),
    path('terms/', views.terms_view, name='terms'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('confirm-receipt/<str:unique_id>/', views.confirm_email_receipt, name='confirm_email_receipt'),
    # Add these new authentication paths
    path('accounts/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
