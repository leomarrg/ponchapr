# encuestas/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import RespuestaEncuesta

@admin.register(RespuestaEncuesta)
class RespuestaEncuestaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'creado_en_formateado', 
        'evaluacion_indice_bienestar', 
        'evaluacion_tendencias_laborales',
        'evaluacion_panel_emprender',
        'evaluacion_plan_decenal', 
        'evaluacion_panel_bigeneracional',
        'promedio_display',
        'completa_display',
        'comentarios_preview'
    ]
    list_filter = [
        'creado_en', 
        'evaluacion_indice_bienestar', 
        'evaluacion_tendencias_laborales',
        'evaluacion_panel_emprender',
        'evaluacion_plan_decenal',
        'evaluacion_panel_bigeneracional'
    ]
    readonly_fields = ['creado_en', 'ip_address', 'user_agent', 'calificacion_promedio']
    search_fields = ['comentarios']
    date_hierarchy = 'creado_en'
    
    fieldsets = (
        ('Evaluaciones por Presentación', {
            'fields': (
                'evaluacion_indice_bienestar',
                'evaluacion_tendencias_laborales', 
                'evaluacion_panel_emprender',
                'evaluacion_plan_decenal',
                'evaluacion_panel_bigeneracional'
            ),
            'description': 'Evaluación de cada presentación del Primer Conversatorio para la Erradicación de la Pobreza Infantil'
        }),
        ('Comentarios Obligatorios', {
            'fields': ('comentarios',),
            'description': 'Comentarios y sugerencias del participante (campo obligatorio)'
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'ip_address', 'user_agent', 'calificacion_promedio'),
            'classes': ('collapse',)
        }),
    )
    
    def creado_en_formateado(self, obj):
        return obj.creado_en.strftime('%d/%m/%Y %H:%M')
    creado_en_formateado.short_description = 'Fecha y Hora'
    
    def promedio_display(self, obj):
        promedio = obj.calificacion_promedio()
        if promedio >= 2.5:
            color = 'green'
        elif promedio >= 2:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, promedio
        )
    promedio_display.short_description = 'Promedio'
    
    def completa_display(self, obj):
        if obj.esta_completa():
            return format_html('<span style="color: green;">✓ Completa</span>')
        else:
            return format_html('<span style="color: red;">✗ Incompleta</span>')
    completa_display.short_description = 'Estado'
    
    def comentarios_preview(self, obj):
        if obj.comentarios:
            preview = obj.comentarios[:50] + '...' if len(obj.comentarios) > 50 else obj.comentarios
            return format_html('<span title="{}">{}</span>', obj.comentarios, preview)
        return format_html('<span style="color: #ccc;">Sin comentarios</span>')
    comentarios_preview.short_description = 'Comentarios (Vista Previa)'