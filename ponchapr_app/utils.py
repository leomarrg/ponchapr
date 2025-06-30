# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags
# from django.conf import settings
# import threading
# import subprocess
# import os
'''
def send_registration_email(attendee, unique_id):
    """
    Send a registration confirmation email to an attendee synchronously
    
    Args:
        attendee: The Attendee object
        unique_id: The unique identifier for checkout (6-digit number)
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    try:
        # Create the email subject
        subject = 'Confirmación de Registro - Su número de identificación único'
        from_email = settings.EMAIL_HOST_USER
        to_email = attendee.email
        
        # Generate the email content with HTML
        html_content = render_to_string('ponchapr_app/email/registration_confirmation.html', {
            'attendee': attendee,
            'unique_id': unique_id
        })
        
        # Generate plain text version
        text_content = strip_tags(html_content)
        
        # Create the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email]
        )
        
        # Attach the HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send()
        print(f"Email sent successfully to {to_email}")
        
        return True
    except Exception as e:
        print(f"Error sending registration email: {e}")
        return False

def send_registration_email_async(attendee, unique_id):
    """
    Asynchronously send a confirmation email to the attendee with their unique ID
    
    Args:
        attendee: The Attendee object
        unique_id: The unique identifier for checkout (6-digit number)
    """
    # Since threading doesn't work well in PythonAnywhere, use the command method instead
    return schedule_registration_email(attendee, unique_id)

def schedule_registration_email(attendee, unique_id):
    """
    Schedule an email to be sent using subprocess to run in the background
    """
    try:
        # Get the project directory
        project_dir = settings.BASE_DIR
        
        # Construct the command to run in the background
        command = f"cd {project_dir} && nohup python3 manage.py send_email {attendee.id} {unique_id} > /tmp/email_log_{attendee.id}.log 2>&1 &"
        
        print(f"Running command: {command}")
        
        # Execute the command in the background
        subprocess.Popen(command, shell=True)
        
        return True
    except Exception as e:
        print(f"Error scheduling email task: {e}")
        return False
'''

"""
def send_registration_email(attendee, unique_id):
    # Función original comentada - mantenida para referencia
    pass

def send_registration_email_async(attendee, unique_id):
    # Función original comentada - mantenida para referencia
    pass

def schedule_registration_email(attendee, unique_id):
    # Función original comentada - mantenida para referencia
    pass
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

# Setup logging
logger = logging.getLogger(__name__)

def send_welcome_email(attendee):
    """
    Send welcome email to an attendee synchronously
    """
    try:
        subject = 'Bienvenido al 1er Conversatorio de la Erradicación para la Pobreza Infantil en Puerto Rico'
        from_email = settings.EMAIL_HOST_USER
        to_email = attendee.email
        
        # Inicializar variables
        html_content = None
        text_content = ""
        
        # Intentar cargar el template HTML
        try:
            html_content = render_to_string('ponchapr_app/email/welcome_email.html', {
                'attendee': attendee,
                'event_name': '1er Conversatorio de la Erradicación para la Pobreza Infantil en Puerto Rico',
                'event_date': attendee.event.date if attendee.event else None,
            })
            text_content = strip_tags(html_content)
            print("✅ Template HTML cargado correctamente")
        except Exception as e:
            print(f"❌ Error cargando template HTML: {e}")
            # Fallback a contenido de texto simple
            text_content = f"""
Estimado/a {attendee.name} {attendee.last_name},

¡Gracias por registrarte en nuestro evento "Primer Conversatorio de la Erradicación para la Pobreza Infantil en Puerto Rico"!

Detalles de tu registro:
- Nombre: {attendee.name} {attendee.last_name}
- Organización: {attendee.organization}
- Email: {attendee.email}
- Teléfono: {attendee.phone_number}
- Fecha de registro: {attendee.created_at.strftime('%d/%m/%Y %H:%M')}

Tu registro ha sido confirmado exitosamente. Esperamos contar contigo en este importante evento.

¡Esperamos verte pronto!

Atentamente,
Departamento de la Familia
"""
            html_content = None
        
        # Crear el correo
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email]
        )
        
        # Agregar contenido HTML si está disponible
        if html_content:
            email.attach_alternative(html_content, "text/html")
        
        # Enviar el correo
        email.send()
        logger.info(f"Correo de bienvenida enviado exitosamente a {to_email}")
        print(f"Correo de bienvenida enviado exitosamente a {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo de bienvenida a {attendee.email}: {str(e)}")
        print(f"Error enviando correo de bienvenida: {str(e)}")

        return False
    
def send_pre_registration_email(attendee):
    """
    Send pre-registration confirmation email to an attendee
    """
    try:
        subject = 'Pre-Registro Confirmado - 1er Conversatorio para la Erradicación de la Pobreza Infantil'
        from_email = settings.EMAIL_HOST_USER
        to_email = attendee.email
        
        # Inicializar variables
        html_content = None
        text_content = ""
        
        # Intentar cargar el template HTML específico para pre-registro
        try:
            html_content = render_to_string('ponchapr_app/email/pre_registration_email.html', {
                'attendee': attendee,
            })
            text_content = strip_tags(html_content)
            print("✅ Template de pre-registro HTML cargado correctamente")
        except Exception as e:
            print(f"❌ Error cargando template de pre-registro HTML: {e}")
            # Fallback a contenido de texto simple específico para pre-registro
            text_content = f"""
Estimado/a {attendee.name} {attendee.last_name},

¡Gracias por completar el pre-registro del 1er Conversatorio para la Erradicación de la Pobreza Infantil en Puerto Rico! 

Te esperamos este lunes, 30 de junio de 2025 en el Salón Royal del Hotel Hilton Garden, a partir de las 8:00 A.M.

Detalles de tu pre-registro:
- Nombre: {attendee.name} {attendee.last_name}
- Organización: {attendee.organization}
- Email: {attendee.email}
- Teléfono: {attendee.phone_number}
- Fecha de pre-registro: {attendee.created_at.strftime('%d/%m/%Y %H:%M')}

¡Esperamos contar con tu valiosa participación!

Cordialmente,
Equipo Organizador
1er Conversatorio para la Erradicación de la Pobreza Infantil
ADSEF - Gobierno de Puerto Rico
"""
            html_content = None
        
        # Crear el correo
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [to_email]
        )
        
        # Agregar contenido HTML si está disponible
        if html_content:
            email.attach_alternative(html_content, "text/html")
        
        # Enviar el correo
        email.send()
        logger.info(f"Correo de pre-registro enviado exitosamente a {to_email}")
        print(f"Correo de pre-registro enviado exitosamente a {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo de pre-registro a {attendee.email}: {str(e)}")
        print(f"Error enviando correo de pre-registro: {str(e)}")
        return False

def send_welcome_email_async(attendee):
    """
    Send welcome email (now synchronous for reliability)
    """
    return send_welcome_email(attendee)

def schedule_welcome_email(attendee):
    """
    Schedule welcome email (now synchronous for reliability)
    """
    return send_welcome_email(attendee)