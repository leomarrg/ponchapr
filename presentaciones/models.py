from django.db import models
from django.utils import timezone

class Administracion(models.Model):
    TIPOS_CHOICES = [
        ('adfan', 'Administración de Familias y Niños (ADFAN)'),
        ('acuden', 'Administración para el Cuidado y Desarrollo Integral de la Niñez (ACUDEN)'),
        ('adsef', 'Administración de Desarrollo Socioeconómico de la Familia (ADSEF)'),
        ('asume', 'Administración para el Sustento de Menores (ASUME)'),
        ('secretariado', 'Secretariado del Departamento de la Familia'),
        ('ofi de lic.', 'Oficina de Licenciamiento'),
        ('procurador', 'Programa Estatal del Procurador de Cuidado a Larga Duración'),
        ('TRUC+', 'Proyecto TRUC+'),
        ('emergency grant', 'Proyecto Emergency Situation Grant'), 
        ('veterando', 'Procurador del Veterano')
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

class VideoBienvenida(models.Model):
    titulo = models.CharField(max_length=200, default="Video de Bienvenida")
    video = models.FileField(upload_to='videos_bienvenida/', help_text="Video de bienvenida del evento")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Video de Bienvenida'
        verbose_name_plural = 'Videos de Bienvenida'
    
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