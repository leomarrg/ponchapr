import os
import subprocess
from django.conf import settings

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