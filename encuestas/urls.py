from django.urls import path
from . import views

app_name = 'encuestas'

urlpatterns = [
    path('', views.formulario_encuesta, name='formulario'),
    path('api/enviar/', views.api_enviar_encuesta, name='api_enviar'),
]