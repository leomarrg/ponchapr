from django import forms
from .models import LocalOffice, Attendee, Review, Region, Event
from datetime import date


class AttendeeForm(forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ['name', 'last_name', 'organization', 'phone_number', 'email']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese su nombre',
                'required': True,
                'id': 'name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ingrese sus apellidos',
                'required': True,
                'id': 'last_name'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la organización o agencia',
                'required': True,
                'id': 'organization'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(787) 123-4567',
                'required': True,
                'id': 'phone_number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@correo.com',
                'required': True,
                'id': 'email'
            })
        }
        
        labels = {
            'name': 'Nombre',
            'last_name': 'Apellidos', 
            'organization': 'Organización/Agencia',
            'phone_number': 'Teléfono',
            'email': 'Correo electrónico'
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remover caracteres no numéricos excepto + al inicio
            import re
            # Mantener solo números, espacios, guiones y paréntesis
            phone = re.sub(r'[^\d\s\-\(\)\+]', '', phone)
            
            # Verificar que tiene al menos 10 dígitos
            digits_only = re.sub(r'[^\d]', '', phone)
            if len(digits_only) < 10:
                raise forms.ValidationError("El número de teléfono debe tener al menos 10 dígitos.")
                
            return phone
        return phone

    # def clean_date_of_birth(self):
    #     birth_date = self.cleaned_data.get('date_of_birth')
    #     if not birth_date:
    #         raise forms.ValidationError("La fecha de nacimiento es requerida")
    #     today = date.today()
    #     if birth_date > today:
    #         raise forms.ValidationError("La fecha de nacimiento no puede estar en el futuro")
    #     return birth_date

    def clean_email(self):
        email = self.cleaned_data.get('email')

        active_event = Event.objects.filter(is_active=True).first()
        
        # Check if email already exists
        if email and active_event:
            existing_attendee = Attendee.objects.filter(email=email, event=active_event).exists()
            if existing_attendee:
                raise forms.ValidationError("Este correo electrónico ya está registrado para este evento.")

        # Check if the email domain is valid
        if email:
            valid_domains = ['pr.gov', 'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
            domain = email.split('@')[-1]
            
            if not any(domain.endswith(valid_domain) for valid_domain in valid_domains):
                raise forms.ValidationError(f"Por favor utilice un correo electrónico con un dominio válido como: {', '.join(valid_domains)}")
        
        return email
    
    def clean_region(self):
        region = self.cleaned_data.get('region')
        if not region:
            raise forms.ValidationError("Por favor seleccione una región")
        return region

class ReviewForm(forms.ModelForm):
    satisfaction = forms.ChoiceField(
        choices=[
            ('Muy satisfecho', 'Muy satisfecho'),
            ('Satisfecho', 'Satisfecho'),
            ('No satisfecho', 'No satisfecho')
        ],
        widget=forms.RadioSelect,
        label="¿Está satisfecho con la información que recibió?",
        required=True,
    )

    usefulness = forms.ChoiceField(
        choices=[
            ('Mucha utilidad', 'Mucha utilidad'),
            ('De utilidad', 'De utilidad'),
            ('No es pertinente a la labor que realizo', 'No es pertinente a la labor que realizo')
        ],
        widget=forms.RadioSelect,
        label="¿La información compartida hoy es de utilidad para la labor que realiza?",
        required=True,
    )

    CATEGORY_CHOICES = [
        ('', 'Seleccione una opción'),  # Placeholder option with empty value
        ('La Musicoterapia: alcance e impacto en metas clínicas desde el arte de la música', 'La Musicoterapia: alcance e impacto en metas clínicas desde el arte de la música'),
        ('Crear una Vida en Balance: Medicina Integrativa', 'Crear una Vida en Balance: Medicina Integrativa')
    ]

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        label="Seleccione una opción",
        required=True
    )
    class Meta:
        model = Review
        fields = ['satisfaction', 'usefulness', 'comments', 'category']
        labels = {
            'satisfaction': "¿Está satisfecho con la información que recibió?",
            'usefulness': "¿La información compartida hoy es de utilidad para la labor que realiza?",
            'comments': 'Comentarios'
        }
        widgets = {
            'comments': forms.Textarea(attrs={'class': 'custom-textarea'}),
        }