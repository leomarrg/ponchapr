from django.contrib import admin
from django.db import models
from .models import Administracion, Presentacion, VideoBienvenida  # Agregado VideoBienvenida

@admin.register(Administracion)
class AdministracionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre', 'codigo']
    list_editable = ['activa']

# NUEVO ADMIN PARA VIDEO DE BIENVENIDA
@admin.register(VideoBienvenida)
class VideoBienvenidaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'activo', 'creado_en']
    list_editable = ['activo']
    
    fieldsets = (
        ('Video de Bienvenida', {
            'fields': ('titulo', 'video', 'activo'),
            'description': 'Administra el video de bienvenida que aparecerá en el portal. Solo puede haber un video activo a la vez.'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.activo:
            # Desactivar otros videos cuando se activa uno nuevo
            VideoBienvenida.objects.exclude(pk=obj.pk).update(activo=False)
        super().save_model(request, obj, form, change)

@admin.register(Presentacion)
class PresentacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'ponente', 'administracion', 'fecha', 'activa', 'orden']
    list_filter = ['administracion', 'fecha', 'activa']
    search_fields = ['titulo', 'ponente']
    list_editable = ['activa', 'orden']
    ordering = ['orden', 'fecha']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'ponente', 'administracion')
        }),
        ('Detalles', {
            'fields': ('fecha', 'duracion_minutos', 'descripcion')
        }),
        ('Archivos', {
            'fields': ('archivo_pdf', 'imagen_thumbnail'),
            'description': 'Sube el PDF de la presentación y una imagen thumbnail.'
        }),
        ('Configuración', {
            'fields': ('activa', 'orden')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            # Auto-asignar orden si no se especifica
            if obj.orden == 0:
                last_orden = Presentacion.objects.aggregate(
                    max_orden=models.Max('orden')
                )['max_orden'] or 0
                obj.orden = last_orden + 1
        super().save_model(request, obj, form, change)