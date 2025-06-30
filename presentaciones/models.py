from django.db import models
from django.utils import timezone

class Administracion(models.Model):
    TIPOS_CHOICES = [
        ('adsef', 'Administración de Desarrollo Socioeconómico de la Familia (ADSEF)'),
        ('comision combatir', 'Comisión para Combatir la Pobreza Infantil y la Desigualdad Social'),
        ('inst desarrollo juv', 'Instituto del Desarrollo de la Juventud'),
        ('MPG PR', 'ManpowerGroup Puerto Rico'),
        ('acuden', 'Administración para el Cuidado y Desarrollo Integral de la Niñez'),
        ('div analisis social', 'División de Análisis Social y Políticas, Estudios Técnicos, Inc.'),
        ('2Gen', 'Centros 2Gen')
    ]
    
    codigo = models.CharField(max_length=20, choices=TIPOS_CHOICES, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Administración'
        verbose_name_plural = 'Administraciones'
    
    def __str__(self):
        return self.nombre

class TipoPresentacion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Tipo de Presentación'
        verbose_name_plural = 'Tipos de Presentación'
    
    def __str__(self):
        return self.nombre

class VideoEvento(models.Model):  # Cambio de VideoBienvenida a VideoEvento
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    video = models.FileField(upload_to='videos_evento/')
    imagen_thumbnail = models.ImageField(upload_to='thumbnails_videos/', blank=True, null=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en el portal")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Video del Evento"
        verbose_name_plural = "Videos del Evento"
        ordering = ['orden', 'creado_en']
    
    def __str__(self):
        return self.titulo

class Presentacion(models.Model):
    titulo = models.CharField(max_length=200)
    ponente = models.CharField(max_length=200)
    administracion = models.ForeignKey(Administracion, on_delete=models.CASCADE)
    fecha = models.DateField()
    duracion_minutos = models.PositiveIntegerField()
    descripcion = models.TextField()
    archivo_pdf = models.FileField(upload_to='presentaciones/', blank=True, null=True)
    imagen_thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    activa = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de aparición en el portal")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['orden', 'fecha']
        verbose_name = 'Presentación'
        verbose_name_plural = 'Presentaciones'
    
    def __str__(self):
        return f"{self.titulo} - {self.ponente}"