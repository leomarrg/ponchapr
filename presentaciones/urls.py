from django.urls import path
from . import views

app_name = 'presentaciones'

urlpatterns = [
    path('', views.portal_presentaciones, name='portal'),
    path('dashboard/', views.dashboard_admin, name='dashboard'),
    path('descargar/<int:presentacion_id>/', views.descargar_presentacion, name='descargar'),
    path('presentacion/<int:presentacion_id>/', views.api_presentacion_detalle, name='api_presentacion'),

    path('informe/pdf/', views.exportar_informe_pdf, name='exportar_pdf'),
]