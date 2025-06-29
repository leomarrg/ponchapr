from django.db import models

class RespuestaEncuesta(models.Model):
    CALIFICACION_CHOICES = [
        ('muy_buena', 'Muy buena'),
        ('buena', 'Buena'),
        ('incompleta', 'Incompleta'),
    ]
    
    # Evaluaciones por administración
    evaluacion_adfan = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="ADFAN"
    )
    evaluacion_acuden = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="ACUDEN"
    )
    evaluacion_adsef = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="ADSEF"
    )
    evaluacion_asume = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="ASUME"
    )
    evaluacion_secretariado = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Secretariado"
    )
    
    # Comentarios
    comentarios = models.TextField(
        blank=True, 
        max_length=1000,
        verbose_name="Comentarios adicionales"
    )
    
    # Metadatos
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Respuesta de Encuesta'
        verbose_name_plural = 'Respuestas de Encuestas'
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"Respuesta {self.id} - {self.creado_en.strftime('%d/%m/%Y %H:%M')}"
    
    def calificacion_promedio(self):
        """Calcula el promedio de calificaciones"""
        calificaciones = [
            self.evaluacion_adfan,
            self.evaluacion_acuden, 
            self.evaluacion_adsef,
            self.evaluacion_asume,
            self.evaluacion_secretariado
        ]
        
        valores = []
        for cal in calificaciones:
            if cal == 'muy_buena':
                valores.append(3)
            elif cal == 'buena':
                valores.append(2)
            elif cal == 'incompleta':
                valores.append(1)
        
        return round(sum(valores) / len(valores), 1) if valores else 0
    
    def esta_completa(self):
        """Verifica si la encuesta está completa"""
        evaluaciones = [
            self.evaluacion_adfan,
            self.evaluacion_acuden,
            self.evaluacion_adsef,
            self.evaluacion_asume,
            self.evaluacion_secretariado
        ]
        return all(evaluaciones)