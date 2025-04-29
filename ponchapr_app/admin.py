from django.contrib import admin
from django.db.models import Count, F, Q
from django.utils.html import format_html
from django.urls import path
from .models import LocalOffice, Event, Attendee, Table, Review, Region
from django.http import HttpResponse
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from .utils import send_registration_email_async



admin.site.site_header = "Panel de Administración RegistratePR"
admin.site.site_title = "Administración de RegistratePR"
admin.site.index_title = "Bienvenido al Panel de Administración"

def export_to_text(modeladmin, request, queryset):
    # Set up the HTTP response with a plain text content type
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="attendees_list.txt"'

    # Loop through each attendee in the queryset and write their info to the response
    for attendee in queryset:
        response.write(f"{attendee.name} {attendee.last_name}\n")  # Customize the fields as needed

    return response

# Add the custom action to your Admin class
export_to_text.short_description = "Export selected attendees to text file"

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        return urls

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
            
        # Get stats for dashboard
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Attendee statistics
        daily_attendees = Attendee.objects.filter(
            registered_at_event__range=(start_date, end_date)
        ).values('registered_at_event__date').annotate(
            count=Count('id')
        ).order_by('registered_at_event__date')

        # Review statistics
        review_stats = Review.objects.values('category').annotate(
            count=Count('id')
        )
        
        extra_context.update({
            'total_attendees': Attendee.objects.count(),
            'arrived_attendees': Attendee.objects.filter(arrived=True).count(),
            'total_reviews': Review.objects.count(),
            'attendee_data': list(daily_attendees.values_list('count', flat=True)),
            'dates': list(daily_attendees.values_list('registered_at_event__date', flat=True)),
            'review_categories': list(review_stats.values_list('category', flat=True)),
            'review_counts': list(review_stats.values_list('count', flat=True)),
        })
        
        return super().index(request, extra_context)

class DuplicateNameFilter(admin.SimpleListFilter):
    title = "Duplicate Names"
    parameter_name = "duplicate_name"
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Show duplicates only'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Find names that appear more than once
            duplicate_names = Attendee.objects.values('name', 'last_name').\
                annotate(name_count=Count('id')).\
                filter(name_count__gt=1)
            
            # Get the names and last names that are duplicated
            duplicate_name_values = [(item['name'], item['last_name']) for item in duplicate_names]
            
            # Filter original queryset to only include these duplicates
            if duplicate_name_values:
                q_objects = Q()
                for name, last_name in duplicate_name_values:
                    q_objects |= Q(name=name, last_name=last_name)
                return queryset.filter(q_objects)
            return queryset.none()
        return queryset


class DuplicatePhoneFilter(admin.SimpleListFilter):
    title = "Duplicate Phone Numbers"
    parameter_name = "duplicate_phone"
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Show duplicates only'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Find phone numbers that appear more than once, excluding empty phones
            duplicate_phones = Attendee.objects.exclude(phone_number='').\
                values('phone_number').\
                annotate(phone_count=Count('id')).\
                filter(phone_count__gt=1)
            
            # Get the phone numbers that are duplicated
            duplicate_phone_values = [item['phone_number'] for item in duplicate_phones]
            
            # Filter original queryset to only include these duplicates
            if duplicate_phone_values:
                return queryset.filter(phone_number__in=duplicate_phone_values)
            return queryset.none()
        return queryset
    

class AttendeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_name', 'email', 'phone_number', 'arrived', 'arrival_time', 'unique_id', 'checkout_time', 'checked_out', 'event')  # Use 'created_at' instead
    list_filter = ('pre_registered', 'registered_at_event', 'arrived', 'arrival_time', DuplicateNameFilter, DuplicatePhoneFilter)
    search_fields = ['name', 'last_name', 'email']

    actions = ['export_to_text', 'resend_email']  # Add to existing actions if any
    
    def resend_email(self, request, queryset):
        success_count = 0
        error_count = 0
        
        for attendee in queryset:
            try:
                # Resend email using your existing email function
                send_registration_email_async(attendee, attendee.unique_id)
                success_count += 1
            except Exception as e:
                self.message_user(request, f"Error sending email to {attendee.email}: {str(e)}", level='ERROR')
                error_count += 1
        
        if success_count:
            self.message_user(request, f"Successfully resent {success_count} email(s).", level='SUCCESS')
        
        if error_count:
            self.message_user(request, f"Failed to send {error_count} email(s). Check logs for details.", level='WARNING')
    
    resend_email.short_description = "Resend confirmation email to selected attendees"

    def resend_email_button(self, obj):
        return format_html('<a class="button" href="{}">Resend Email</a>', 
                         f'/admin/ponchapr_app/attendee/{obj.id}/resend_email/')
    
    resend_email_button.short_description = "Resend Email"
    resend_email_button.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        # Get arrival time statistics for the chart
        arrival_stats = (
            Attendee.objects
            .filter(arrived=True)
            .annotate(hour=ExtractHour('arrival_time'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )

        # Prepare data for the chart
        hours = range(24)
        chart_data = {hour: 0 for hour in hours}
        for stat in arrival_stats:
            chart_data[int(stat['hour'])] = stat['count']

        extra_context = extra_context or {}
        extra_context['arrival_data'] = list(chart_data.values())
        extra_context['hours'] = list(hours)

        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        js = ('admin/js/chart.min.js',)  # Make sure to include Chart.js

    # class Media:
    #     js = ('js/dynamic_search.js',)  # Add the JavaScript for dynamic search

    # Add the autocomplete URL
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/resend_email/', self.admin_site.admin_view(self.resend_individual_email), name='attendee-resend-email'),
            path('<path:object_id>/mark_arrived/', self.admin_site.admin_view(self.mark_arrived), name='attendee-mark-arrived'),
            path('<path:object_id>/unmark_arrived/', self.admin_site.admin_view(self.unmark_arrived), name='attendee-unmark-arrived'),
            path('checkin-qr/', self.admin_site.admin_view(self.checkin_qr_code_verify), name='checkin_qr_code_verify'),
            path('checkout-qr/', self.admin_site.admin_view(self.checkout_qr_code_verify), name='checkout_qr_code_verify'),
        ]
        return custom_urls + urls

    def resend_individual_email(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            try:
                send_registration_email_async(attendee, attendee.unique_id)
                self.message_user(request, f"Email resent successfully to {attendee.email}", level='SUCCESS')
            except Exception as e:
                self.message_user(request, f"Error sending email to {attendee.email}: {str(e)}", level='ERROR')
        return redirect('admin:ponchapr_app_attendee_changelist')
    
    def checkin_qr_code_verify(self, request):
        return render(request, 'admin/ponchapr_app/checkin_qr_code_verify.html')
    
    def checkout_qr_code_verify(self, request):
        return render(request, 'admin/ponchapr_app/checkout_qr_code_verify.html')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_scan_buttons'] = True
        return super().changelist_view(request, extra_context=extra_context)
    
    def mark_checkout(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.checked_out = True
            attendee.checkout_time = timezone.now()  # Make sure this line is present!
            attendee.save()
        return redirect('admin:ponchapr_app_attendee_changelist')
    

    # def autocomplete_view(self, request):
    #     if 'term' in request.GET:
    #         term = request.GET.get('term')
    #         # Use 'istartswith' for prefix-based matching
    #         qs = Attendee.objects.filter(name__istartswith=term) | Attendee.objects.filter(last_name__istartswith=term)
    #         attendees = list(qs.values('id', 'name'))
    #         return JsonResponse(attendees, safe=False)

    #     return JsonResponse([], safe=False)

    def registration_type(self, obj):
        if obj.pre_registered:
            return "Pre-Registered"
        elif obj.registered_at_event:
            return "Same-Day Registered"
        return "Unknown"

    registration_type.short_description = "Registration Type"

    # Custom buttons to mark/unmark attendees as arrived
    def mark_as_arrived_button(self, obj):
        if not obj.arrived:
            return format_html('<a class="button" href="{}">Mark as Arrived</a>', 
                             f'/admin/ponchapr_app/attendee/{obj.id}/mark_arrived/')
        else:
            return format_html('<a class="button" href="{}">Unmark as Arrived</a>', 
                             f'/admin/ponchapr_app/attendee/{obj.id}/unmark_arrived/')
    mark_as_arrived_button.short_description = "Mark/Unmark as Arrived"
    mark_as_arrived_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/mark_arrived/', self.admin_site.admin_view(self.mark_arrived), name='attendee-mark-arrived'),
            path('<path:object_id>/unmark_arrived/', self.admin_site.admin_view(self.unmark_arrived), name='attendee-unmark-arrived'),
        ]
        return custom_urls + urls

    def mark_arrived(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.arrived = True
            attendee.arrival_time = timezone.now()  # Set timestamp when marking as arrived
            attendee.save()
        return redirect('admin:ponchapr_app_attendee_changelist')

    def unmark_arrived(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.arrived = False
            attendee.arrival_time = None  # Clear timestamp when unmarking
            attendee.save()
        return redirect('admin:ponchapr_app_attendee_changelist')

    def get_available_seat(self):
        # Logic to get the next available seat in a table
        available_table = Table.objects.annotate(
            attendee_count=Count('attendee')
        ).filter(
            attendee_count__lt=F('max_seats')
        ).first()

        if available_table:
            assigned_seats = Attendee.objects.filter(table=available_table).values_list('seat_number', flat=True)
            available_seat = next((seat for seat in range(1, available_table.max_seats + 1) if seat not in assigned_seats), None)
            if available_seat is not None:
                return available_table, available_seat

        return None, None  # If no seats are available
    
    @staff_member_required
    def qr_code_verify(request):
        return render(request, 'admin/ponchapr_app/qr_code_verify.html')

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('name',)
    actions = ['make_active']
    
    def make_active(self, request, queryset):
        # Solo activar el primer evento seleccionado
        if queryset.count() > 0:
            first_event = queryset.first()
            # Desactivar todos los eventos
            Event.objects.all().update(is_active=False)
            # Activar el seleccionado
            first_event.is_active = True
            first_event.save()
            self.message_user(request, f"Evento '{first_event}' marcado como activo")
    
    make_active.short_description = "Marcar evento seleccionado como activo"

class LocalOfficeAdmin(admin.ModelAdmin):
    list_display = ('office_name', 'region', 'rmo')
    list_filter = ('region',)
    search_fields = ('office_name', 'rmo')
    ordering = ('region', 'office_name')

class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'offices_count')
    search_fields = ('name',)
    list_filter = ('active',)
    
    def offices_count(self, obj):
        return obj.offices.count()
    
    offices_count.short_description = 'Número de Oficinas'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('satisfaction', 'usefulness', 'category', 'comments', 'review_date')
    fields = ('satisfaction', 'usefulness', 'category', 'comments', 'review_date')  # Include 'category' in the detail view

    actions = ['export_reviews_to_txt']

    def export_reviews_to_txt(self, request, queryset):
        # Create the HttpResponse object with plain text content
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="reviews.txt"'

        # Write the selected reviews to the response
        for review in queryset:
            response.write(
                f"Satisfaction: {review.satisfaction}\n"
                f"Usefulness: {review.usefulness}\n"
                f"Category: {review.category}\n"
                f"Comments: {review.comments}\n"
                f"Review Date: {review.review_date}\n\n"
            )

        return response

    export_reviews_to_txt.short_description = "Export selected reviews to text file"
    # Restringir permisos de edición
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('registry_app.change_review')


class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    search_fields = ('name',)
    list_filter = ('active',)

admin.site.register(Region, RegionAdmin)
# @admin.register(FileDownload)
# class FileDownloadAdmin(admin.ModelAdmin):
#     list_display = ('file', 'display_name', 'download_count')  # Add display_name here
#     list_editable = ('display_name',)  # Allow editing directly in the list view
#     search_fields = ('file', 'display_name')  # Enable search functionality
#     list_filter = ('download_count',)

admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(LocalOffice, LocalOfficeAdmin)

