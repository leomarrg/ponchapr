# tasks.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_email_task(attendee_id, unique_id):
    """
    Task to send an email in the background
    """
    from .models import Attendee  # Import here to avoid circular imports
    
    try:
        attendee = Attendee.objects.get(id=attendee_id)
        
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