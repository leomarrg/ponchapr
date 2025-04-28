from django.db import models
import uuid
from django.utils import timezone


# Create your models here.
# registry_app/models.py

class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.date})"
    
    class Meta:
        ordering = ['-date']
    
    def save(self, *args, **kwargs):
        # Si este evento se está marcando como activo, desactivar los demás
        if self.is_active:
            Event.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

class Table(models.Model):
    table_number = models.PositiveIntegerField(unique=True)
    max_seats = models.PositiveIntegerField(default=5)  # Add max_seats field with a default value

    def __str__(self):
        return f"Table {self.table_number}"

    def current_attendees_count(self):
        return self.attendee_set.filter(arrived=True).count()

    def has_available_seat(self):
        return self.current_attendees_count() < self.max_seats
    
class FileDownload(models.Model):
    file = models.FileField(upload_to='files/', default='files/placeholder.txt')  # Add default value
    download_count = models.PositiveIntegerField(default=0)
    display_name = models.TextField(blank=True, null=True)
    is_video = models.BooleanField(default=False)

    def __str__(self):
        return str(self.display_name) if self.display_name else str(self.file)

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Attendee(models.Model):
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True)
    
    # New unique identifier field (6-digit number)
    unique_id = models.CharField(max_length=6, unique=True, blank=True)
    
    # QR code (legacy field can be reused or kept for compatibility)
    qr_code_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Registration status
    pre_registered = models.BooleanField(default=False)
    registered_at_event = models.BooleanField(default=False)
    
    # Check-in/out status and timestamps
    arrived = models.BooleanField(default=False)
    arrival_time = models.DateTimeField(null=True, blank=True)
    checked_out = models.BooleanField(default=False)
    checkout_time = models.DateTimeField(null=True, blank=True)
    
    # Added region field
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['email', 'event']]
    
    def __str__(self):
        return f"{self.name} {self.last_name}"
    
    def generate_unique_id(self):
        """Generate a 6-digit unique identifier"""
        import random
        import string
        while True:
            unique_id = ''.join(random.choices(string.digits, k=6))
            if not type(self).objects.filter(unique_id=unique_id).exists():
                return unique_id

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        
        if self.checked_out and not self.checkout_time:
            self.checkout_time = timezone.now()
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add just the QR code ID
        qr.add_data(str(self.qr_code_id))
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return str(self.unique_id)

    def __str__(self):
        return f"{self.name} {self.last_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    # def assign_table_and_seat(self):
    #     # Get all tables sorted by the number of attendees assigned
    #     tables = Table.objects.all()
    #     tables = sorted(tables, key=lambda t: t.current_attendees_count())

    #     # Find the first available table with fewer attendees than max seats
    #     for table in tables:
    #         if table.has_available_seat():
    #             self.table = table
    #             self.seat_number = table.current_attendees_count() + 1
    #             break

class Review(models.Model):
    comments = models.TextField()
    satisfaction = models.CharField(max_length=50)  # This field should be present
    usefulness = models.CharField(max_length=50)    # This field should be present
    review_date = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=1000)


    def __str__(self):
        return f"Satisfaction: {self.satisfaction}, Usefulness: {self.usefulness}, Category: {self.category}, Date: {self.review_date}"