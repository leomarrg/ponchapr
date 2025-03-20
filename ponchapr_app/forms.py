from django import forms
from .models import Attendee, Review, Region
from datetime import date


class AttendeeForm(forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ['name', 'last_name', 'phone_number', 'email', 'region']
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'name',
                'required': True,
            }),
            'last_name': forms.TextInput(attrs={
                'id': 'last-name',
                'required': True,
            }),
            'phone_number': forms.TextInput(attrs={
                'id': 'phone',
                'pattern': '[0-9]{3}-[0-9]{3}-[0-9]{4}',
                'placeholder': '123-456-7890',
                'required': True,
            }),
            # 'date_of_birth': forms.DateInput(attrs={
            #     'id': 'date-of-birth',
            #     'type': 'date',
            #     'placeholder': 'mm-dd-yyyy',
            #     'required': True,
            # }),
            'email': forms.EmailInput(attrs={
                'id': 'email',
                'required': True,
            }),
            'region': forms.Select(attrs={
                'id': 'region',
                'required': True,
            }),
        }
        labels = {
            'name': 'Nombre',
            'last_name': 'Apellidos',
            'phone_number': 'Número de teléfono',
            # 'date_of_birth': 'Fecha de nacimiento',
            'email': 'Correo electrónico',
            'region': 'Región',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].widget.attrs['type'] = 'tel'
        # self.fields['date_of_birth'].widget.attrs['type'] = 'date'
        self.fields['region'].queryset = Region.objects.filter(active=True)
        self.fields['region'].empty_label = "Seleccione una región"

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) != 10:
                raise forms.ValidationError("El número de teléfono debe contener exactamente 10 dígitos")
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
        if Attendee.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
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