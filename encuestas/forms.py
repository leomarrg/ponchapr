from django import forms
from .models import RespuestaEncuesta

class EncuestaForm(forms.ModelForm):
    class Meta:
        model = RespuestaEncuesta
        fields = [
            'evaluacion_adfan',
            'evaluacion_acuden', 
            'evaluacion_adsef',
            'evaluacion_asume',
            'evaluacion_secretariado',
            'comentarios'
        ]
        
        widgets = {
            'evaluacion_adfan': forms.RadioSelect(),
            'evaluacion_acuden': forms.RadioSelect(),
            'evaluacion_adsef': forms.RadioSelect(),
            'evaluacion_asume': forms.RadioSelect(),
            'evaluacion_secretariado': forms.RadioSelect(),
            'comentarios': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Escriba aquí sus comentarios, sugerencias o solicitudes de información adicional...',
                'maxlength': 1000
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar campos requeridos
        required_fields = [
            'evaluacion_adfan',
            'evaluacion_acuden', 
            'evaluacion_adsef',
            'evaluacion_asume',
            'evaluacion_secretariado'
        ]
        
        for field_name in required_fields:
            self.fields[field_name].required = True