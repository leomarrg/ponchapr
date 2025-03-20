from django.core.management.base import BaseCommand
from ponchapr_app.models import Attendee
from ponchapr_app.utils import send_registration_email

class Command(BaseCommand):
    help = 'Sends a registration confirmation email'

    def add_arguments(self, parser):
        parser.add_argument('attendee_id', type=int)
        parser.add_argument('unique_id', type=str)

    def handle(self, *args, **options):
        attendee_id = options['attendee_id']
        unique_id = options['unique_id']
        
        try:
            attendee = Attendee.objects.get(id=attendee_id)
            result = send_registration_email(attendee, unique_id)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f'Email sent successfully to {attendee.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send email to {attendee.email}'))
        except Attendee.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Attendee with ID {attendee_id} not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))