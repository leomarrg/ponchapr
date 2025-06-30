# encuestas/models.py
from django.db import models

class RespuestaEncuesta(models.Model):
    CALIFICACION_CHOICES = [
        ('muy_buena', 'Muy buena'),
        ('buena', 'Buena'),
        ('incompleta', 'Incompleta'),
    ]
    
    # Nuevas evaluaciones por presentación
    evaluacion_indice_bienestar = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Índice de Bienestar de la Niñez y la Juventud"
    )
    evaluacion_tendencias_laborales = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Tendencias Laborales en Puerto Rico"
    )
    evaluacion_panel_emprender = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Panel: Apoyos y Oportunidades para Emprender"
    )
    evaluacion_plan_decenal = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Plan Decenal para Combatir la Pobreza Infantil"
    )
    evaluacion_panel_bigeneracional = models.CharField(
        max_length=20, 
        choices=CALIFICACION_CHOICES, 
        blank=True,
        verbose_name="Panel: Iniciativas Bigeneracionales"
    )
    
    # Comentarios ahora obligatorios
    comentarios = models.TextField(
        max_length=1000,
        verbose_name="Comentarios adicionales",
        help_text="Campo obligatorio: Comparta sus comentarios, sugerencias o solicitudes de información adicional"
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
            self.evaluacion_indice_bienestar,
            self.evaluacion_tendencias_laborales, 
            self.evaluacion_panel_emprender,
            self.evaluacion_plan_decenal,
            self.evaluacion_panel_bigeneracional
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
            self.evaluacion_indice_bienestar,
            self.evaluacion_tendencias_laborales,
            self.evaluacion_panel_emprender,
            self.evaluacion_plan_decenal,
            self.evaluacion_panel_bigeneracional
        ]
        return all(evaluaciones) and bool(self.comentarios and self.comentarios.strip())