from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading

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
    def send_email():
        try:
            # Use the synchronous function inside the thread
            result = send_registration_email(attendee, unique_id)
            print(f"Asynchronous email sending result: {result}")
            return result
        except Exception as e:
            print(f"Error in async email thread: {e}")
            return False
    
    # Start email sending in a separate thread
    print(f"Starting email thread for {attendee.email} with ID {unique_id}")
    email_thread = threading.Thread(target=send_email)
    email_thread.start()
    
    return True  # Return immediately since we're using threading