# encuestas/forms.py
from django import forms
from .models import RespuestaEncuesta

class EncuestaForm(forms.ModelForm):
    class Meta:
        model = RespuestaEncuesta
        fields = [
            'evaluacion_indice_bienestar',
            'evaluacion_tendencias_laborales', 
            'evaluacion_panel_emprender',
            'evaluacion_plan_decenal',
            'evaluacion_panel_bigeneracional',
            'comentarios'
        ]
        
        widgets = {
            'evaluacion_indice_bienestar': forms.RadioSelect(),
            'evaluacion_tendencias_laborales': forms.RadioSelect(),
            'evaluacion_panel_emprender': forms.RadioSelect(),
            'evaluacion_plan_decenal': forms.RadioSelect(),
            'evaluacion_panel_bigeneracional': forms.RadioSelect(),
            'comentarios': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Escriba aquí sus comentarios, sugerencias o solicitudes de información adicional sobre las presentaciones del conversatorio...',
                'maxlength': 1000,
                'required': True
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar todos los campos como requeridos
        required_fields = [
            'evaluacion_indice_bienestar',
            'evaluacion_tendencias_laborales', 
            'evaluacion_panel_emprender',
            'evaluacion_plan_decenal',
            'evaluacion_panel_bigeneracional',
            'comentarios'
        ]
        
        for field_name in required_fields:
            self.fields[field_name].required = True
            
        # Agregar clase CSS al campo de comentarios
        self.fields['comentarios'].widget.attrs.update({
            'class': 'form-control comments-textarea'
        })
    
    def clean_comentarios(self):
        comentarios = self.cleaned_data.get('comentarios')
        if not comentarios or not comentarios.strip():
            raise forms.ValidationError("Los comentarios son obligatorios. Por favor, comparta su opinión sobre las presentaciones.")
        
        if len(comentarios.strip()) < 10:
            raise forms.ValidationError("Por favor, proporcione comentarios más detallados (mínimo 10 caracteres).")
            
        return comentarios.strip()