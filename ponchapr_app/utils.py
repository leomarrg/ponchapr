from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading
import subprocess
import os

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
        html_content = render_to_string('ponchapr_app/email/email_confirmed.html', {
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