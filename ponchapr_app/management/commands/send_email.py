# ponchapr_app/management/commands/send_welcome_email.py

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from ponchapr_app.models import Attendee

class Command(BaseCommand):
    help = 'Send welcome email to an attendee'

    def add_arguments(self, parser):
        parser.add_argument('attendee_id', type=int, help='The ID of the attendee')

    def handle(self, *args, **options):
        attendee_id = options['attendee_id']
        
        try:
            attendee = Attendee.objects.get(id=attendee_id)
            
            # Create the email subject
            subject = 'Bienvenido al Evento ADSEF - Confirmación de Registro'
            from_email = settings.EMAIL_HOST_USER
            to_email = attendee.email
            
            # Generate the email content with HTML
            html_content = render_to_string('ponchapr_app/email/welcome_email.html', {
                'attendee': attendee,
                'event_name': 'Compromiso en Acción - ADSEF',
                'event_date': attendee.event.date if attendee.event else None,
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
            
            self.stdout.write(
                self.style.SUCCESS(f'Welcome email sent successfully to {to_email}')
            )
            
        except Attendee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Attendee with ID {attendee_id} does not exist')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending welcome email: {str(e)}')
            )