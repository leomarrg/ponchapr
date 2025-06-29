from django.contrib import admin
from django.utils.html import format_html
from .models import RespuestaEncuesta

@admin.register(RespuestaEncuesta)
class RespuestaEncuestaAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'creado_en_formateado', 
        'evaluacion_adfan', 
        'evaluacion_acuden',
        'evaluacion_adsef',
        'evaluacion_asume', 
        'evaluacion_secretariado',
        'promedio_display',
        'completa_display'
    ]
    list_filter = [
        'creado_en', 
        'evaluacion_adfan', 
        'evaluacion_acuden',
        'evaluacion_adsef',
        'evaluacion_asume',
        'evaluacion_secretariado'
    ]
    readonly_fields = ['creado_en', 'ip_address', 'user_agent', 'calificacion_promedio']
    search_fields = ['comentarios']
    date_hierarchy = 'creado_en'
    
    fieldsets = (
        ('Evaluaciones por Administración', {
            'fields': (
                'evaluacion_adfan',
                'evaluacion_acuden', 
                'evaluacion_adsef',
                'evaluacion_asume',
                'evaluacion_secretariado'
            )
        }),
        ('Comentarios', {
            'fields': ('comentarios',)
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