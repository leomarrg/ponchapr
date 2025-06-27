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
from .utils import send_welcome_email_async, send_pre_registration_email, send_welcome_email  # ← Imports completos
from datetime import timedelta

admin.site.site_header = "Panel de Administración ADSEF"
admin.site.site_title = "Administración de ADSEF"
admin.site.index_title = "Bienvenido al Panel de Administración"

def export_to_text(modeladmin, request, queryset):
    # Set up the HTTP response with a plain text content type
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="participantes_lista.txt"'

    # Loop through each attendee in the queryset and write their info to the response
    for attendee in queryset:
        response.write(f"{attendee.name} {attendee.last_name} - {attendee.organization} - {attendee.email} - {attendee.phone_number}\n")

    return response

# Add the custom action to your Admin class
export_to_text.short_description = "Exportar participantes seleccionados a archivo de texto"

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
            created_at__range=(start_date, end_date)
        ).values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')

        # Review statistics
        review_stats = Review.objects.values('category').annotate(
            count=Count('id')
        )
        
        extra_context.update({
            'total_attendees': Attendee.objects.count(),
            'arrived_attendees': Attendee.objects.filter(arrived=True).count(),
            'total_reviews': Review.objects.count(),
            'attendee_data': list(daily_attendees.values_list('count', flat=True)),
            'dates': list(daily_attendees.values_list('created_at__date', flat=True)),
            'review_categories': list(review_stats.values_list('category', flat=True)),
            'review_counts': list(review_stats.values_list('count', flat=True)),
        })
        
        return super().index(request, extra_context)

class DuplicateNameFilter(admin.SimpleListFilter):
    title = "Nombres Duplicados"
    parameter_name = "duplicate_name"
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Mostrar solo duplicados'),
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

class DuplicateEmailFilter(admin.SimpleListFilter):
    title = "Correos Duplicados"
    parameter_name = "duplicate_email"
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Mostrar solo duplicados'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            # Find emails that appear more than once
            duplicate_emails = Attendee.objects.exclude(email='').\
                values('email').\
                annotate(email_count=Count('id')).\
                filter(email_count__gt=1)
            
            # Get the emails that are duplicated
            duplicate_email_values = [item['email'] for item in duplicate_emails]
            
            # Filter original queryset to only include these duplicates
            if duplicate_email_values:
                return queryset.filter(email__in=duplicate_email_values)
            return queryset.none()
        return queryset

class DuplicatePhoneFilter(admin.SimpleListFilter):
    title = "Teléfonos Duplicados"
    parameter_name = "duplicate_phone"
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Mostrar solo duplicados'),
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

class OrganizationFilter(admin.SimpleListFilter):
    title = "Organización/Agencia"
    parameter_name = "organization"
    
    def lookups(self, request, model_admin):
        try:
            organizations = Attendee.objects.exclude(organization='').exclude(organization__isnull=True).values_list('organization', flat=True).distinct()
            return [(org, org) for org in organizations if org]
        except Exception:
            return []
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(organization=self.value())
        return queryset

class AttendeeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'last_name', 
        'organization', 
        'email', 
        'phone_number', 
        'arrived', 
        'arrival_time', 
        'checkout_time', 
        'checked_out', 
        'event',
        'created_at'
    )
    
    list_filter = (
        'pre_registered', 
        'registered_at_event', 
        'arrived', 
        'checked_out',
        'created_at',
        OrganizationFilter,
        DuplicateNameFilter, 
        DuplicateEmailFilter,
        DuplicatePhoneFilter,
        'event'
    )
    
    search_fields = ['name', 'last_name', 'email', 'organization', 'phone_number']
    
    readonly_fields = ('unique_id', 'qr_code_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('name', 'last_name', 'organization', 'email', 'phone_number')
        }),
        ('Información del Evento', {
            'fields': ('event', 'unique_id', 'qr_code_id')
        }),
        ('Estado de Registro', {
            'fields': ('pre_registered', 'registered_at_event')
        }),
        ('Estado de Asistencia', {
            'fields': ('arrived', 'arrival_time', 'checked_out', 'checkout_time')
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['export_to_text', 'resend_email', 'mark_as_arrived', 'mark_as_not_arrived']
    
    def resend_email(self, request, queryset):
        success_count = 0
        error_count = 0
        
        for attendee in queryset:
            try:
                # Usar la función correcta según el tipo de registro
                if attendee.pre_registered:
                    send_pre_registration_email(attendee)
                else:
                    send_welcome_email(attendee)
                success_count += 1
            except Exception as e:
                self.message_user(request, f"Error enviando correo a {attendee.email}: {str(e)}", level='ERROR')
                error_count += 1
        
        if success_count:
            self.message_user(request, f"Se reenviaron exitosamente {success_count} correo(s).", level='SUCCESS')
        
        if error_count:
            self.message_user(request, f"Falló el envío de {error_count} correo(s). Revise los logs para más detalles.", level='WARNING')
    
    resend_email.short_description = "Reenviar correo a participantes seleccionados"
    
    def mark_as_arrived(self, request, queryset):
        updated = 0
        for attendee in queryset:
            if not attendee.arrived:
                attendee.arrived = True
                attendee.arrival_time = timezone.now()
                attendee.save()
                updated += 1
        
        self.message_user(request, f"Se marcaron como llegados {updated} participante(s).", level='SUCCESS')
    
    mark_as_arrived.short_description = "Marcar como llegados"
    
    def mark_as_not_arrived(self, request, queryset):
        updated = 0
        for attendee in queryset:
            if attendee.arrived:
                attendee.arrived = False
                attendee.arrival_time = None
                attendee.save()
                updated += 1
        
        self.message_user(request, f"Se desmarcaron como llegados {updated} participante(s).", level='SUCCESS')
    
    mark_as_not_arrived.short_description = "Desmarcar como llegados"

    def resend_email_button(self, obj):
        return format_html('<a class="button" href="{}">Reenviar Correo</a>', 
                         f'/admin/ponchapr_app/attendee/{obj.id}/resend_email/')
    
    resend_email_button.short_description = "Reenviar Correo"
    resend_email_button.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        try:
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
                if stat['hour'] is not None:
                    chart_data[int(stat['hour'])] = stat['count']

            # Get organization statistics
            org_stats = (
                Attendee.objects
                .exclude(organization='')
                .exclude(organization__isnull=True)
                .values('organization')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]  # Top 10 organizations
            )

            extra_context = extra_context or {}
            extra_context.update({
                'arrival_data': list(chart_data.values()),
                'hours': list(hours),
                'org_stats': list(org_stats),
                'show_scan_buttons': True
            })
        except Exception as e:
            # En caso de error, proporcionar datos vacíos
            extra_context = extra_context or {}
            extra_context.update({
                'arrival_data': [0] * 24,
                'hours': list(range(24)),
                'org_stats': [],
                'show_scan_buttons': True
            })

        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        js = ('admin/js/chart.min.js',)  # Make sure to include Chart.js

    # Add the custom URLs
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
                # Usar la función correcta según el tipo de registro
                if attendee.pre_registered:
                    send_pre_registration_email(attendee)
                    email_type = "pre-registro"
                else:
                    send_welcome_email(attendee)
                    email_type = "bienvenida"
                
                self.message_user(request, f"Correo de {email_type} reenviado exitosamente a {attendee.email}", level='SUCCESS')
            except Exception as e:
                self.message_user(request, f"Error enviando correo a {attendee.email}: {str(e)}", level='ERROR')
        return redirect('admin:ponchapr_app_attendee_changelist')
    
    def checkin_qr_code_verify(self, request):
        return render(request, 'admin/ponchapr_app/checkin_qr_code_verify.html')
    
    def checkout_qr_code_verify(self, request):
        return render(request, 'admin/ponchapr_app/checkout_qr_code_verify.html')
    
    def mark_checkout(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.checked_out = True
            attendee.checkout_time = timezone.now()
            attendee.save()
            self.message_user(request, f"{attendee.name} {attendee.last_name} marcado como checkout exitosamente.", level='SUCCESS')
        return redirect('admin:ponchapr_app_attendee_changelist')

    def registration_type(self, obj):
        if obj.pre_registered:
            return "Pre-Registrado"
        elif obj.registered_at_event:
            return "Registro en Sitio"
        return "Desconocido"

    registration_type.short_description = "Tipo de Registro"

    # Custom buttons to mark/unmark attendees as arrived
    def mark_as_arrived_button(self, obj):
        if not obj.arrived:
            return format_html('<a class="button" href="{}">Marcar como Llegado</a>', 
                             f'/admin/ponchapr_app/attendee/{obj.id}/mark_arrived/')
        else:
            return format_html('<a class="button" href="{}">Desmarcar como Llegado</a>', 
                             f'/admin/ponchapr_app/attendee/{obj.id}/unmark_arrived/')
    mark_as_arrived_button.short_description = "Marcar/Desmarcar Llegada"
    mark_as_arrived_button.allow_tags = True

    def mark_arrived(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.arrived = True
            attendee.arrival_time = timezone.now()
            attendee.save()
            self.message_user(request, f"{attendee.name} {attendee.last_name} marcado como llegado.", level='SUCCESS')
        return redirect('admin:ponchapr_app_attendee_changelist')

    def unmark_arrived(self, request, object_id):
        attendee = self.get_object(request, object_id)
        if attendee:
            attendee.arrived = False
            attendee.arrival_time = None
            attendee.save()
            self.message_user(request, f"{attendee.name} {attendee.last_name} desmarcado como llegado.", level='SUCCESS')
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

        return None, None

class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'end_time', 'is_active', 'attendee_count')
    list_filter = ('is_active', 'date')
    search_fields = ('name',)
    actions = ['make_active']
    
    def attendee_count(self, obj):
        return obj.attendee_set.count()
    attendee_count.short_description = 'Participantes Registrados'
    
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
        try:
            return obj.offices.count()
        except Exception:
            return 0
    
    offices_count.short_description = 'Número de Oficinas'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('satisfaction', 'usefulness', 'category', 'comments', 'review_date')
    fields = ('satisfaction', 'usefulness', 'category', 'comments', 'review_date')
    list_filter = ('satisfaction', 'usefulness', 'category', 'review_date')
    search_fields = ('comments', 'category')
    date_hierarchy = 'review_date'

    actions = ['export_reviews_to_txt']

    def export_reviews_to_txt(self, request, queryset):
        # Create the HttpResponse object with plain text content
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="evaluaciones.txt"'

        # Write the selected reviews to the response
        for review in queryset:
            response.write(
                f"Satisfacción: {review.satisfaction}\n"
                f"Utilidad: {review.usefulness}\n"
                f"Categoría: {review.category}\n"
                f"Comentarios: {review.comments}\n"
                f"Fecha de Evaluación: {review.review_date}\n\n"
                f"{'='*50}\n\n"
            )

        return response

    export_reviews_to_txt.short_description = "Exportar evaluaciones seleccionadas a archivo de texto"

# Register models
admin.site.register(Region, RegionAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(LocalOffice, LocalOfficeAdmin)