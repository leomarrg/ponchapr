from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .forms import EncuestaForm
from .models import RespuestaEncuesta
import json

def formulario_encuesta(request):
    """Formulario de evaluación de presentaciones"""
    if request.method == 'POST':
        form = EncuestaForm(request.POST)
        if form.is_valid():
            respuesta = form.save(commit=False)
            
            # Capturar metadatos de la solicitud
            respuesta.ip_address = get_client_ip(request)
            respuesta.user_agent = request.META.get('HTTP_USER_AGENT', '')
            respuesta.save()
            
            messages.success(
                request, 
                'Su evaluación ha sido enviada exitosamente. ¡Gracias por su participación!'
            )
            return redirect('encuestas:formulario')
        else:
            messages.error(
                request,
                'Por favor, complete la evaluación de todas las administraciones.'
            )
    else:
        form = EncuestaForm()
    
    return render(request, 'encuestas/encuesta_evento.html', {'form': form})

@csrf_exempt
@require_http_methods(["POST"])
def api_enviar_encuesta(request):
    """API para enviar encuesta vía AJAX"""
    try:
        data = json.loads(request.body)
        
        # Crear instancia del formulario con los datos
        form = EncuestaForm(data)
        
        if form.is_valid():
            respuesta = form.save(commit=False)
            respuesta.ip_address = get_client_ip(request)
            respuesta.user_agent = request.META.get('HTTP_USER_AGENT', '')
            respuesta.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Evaluación enviada exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)

def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip