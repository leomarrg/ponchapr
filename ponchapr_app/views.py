from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .forms import AttendeeForm
from .models import Attendee, Event, Region, LocalOffice
from .utils import send_welcome_email_async, send_welcome_email, send_pre_registration_email
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Avg, F, ExpressionWrapper
from django.db.models.functions import TruncHour
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
import json
from io import BytesIO
import logging
from django.db.models import Q, Count
from collections import defaultdict
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

def pre_register(request):
    if request.method == 'POST':
        form = AttendeeForm(request.POST)
        if form.is_valid():
            try:
                # Obtener el evento activo
                active_event = Event.objects.filter(is_active=True).first()
                
                if not active_event:
                    messages.error(request, "No hay un evento activo configurado. Por favor, contacte al administrador.")
                    return render(request, 'ponchapr_app/pre_register.html', {'form': AttendeeForm()})
                
                attendee = form.save(commit=False)
                attendee.pre_registered = True
                attendee.event = active_event  # ← LÍNEA AÑADIDA: Asignar evento activo
                # Para pre-registro, NO marcar como llegado
                attendee.arrived = False
                attendee.save()
                
                # Enviar correo específico de pre-registro (no fallar si hay error)
                try:
                    from .utils import send_pre_registration_email  # Import específico
                    send_pre_registration_email(attendee)
                    email_status = "El correo de confirmación de pre-registro será enviado en breve."
                except Exception as email_error:
                    print(f"Error enviando correo: {email_error}")
                    email_status = "El pre-registro fue exitoso, pero hubo un problema enviando el correo."
                
                messages.success(request, f"¡Pre-registro exitoso! {email_status}")
                return render(request, 'ponchapr_app/pre_register.html', {'form': AttendeeForm()})
                
            except Exception as e:
                print(f"Error en el pre-registro: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Hubo un problema con el pre-registro: {str(e)}")
        else:
            # Procesar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = AttendeeForm()
    
    return render(request, 'ponchapr_app/pre_register.html', {'form': form})
    

def front_desk_register(request):
    """Handle registrations that happen at the event (same day registrations)"""
    
    active_event = Event.objects.filter(is_active=True).first()

    if not active_event:
        messages.error(request, "No hay un evento activo configurado. Por favor, contacte al administrador.")
        return render(request, 'ponchapr_app/register.html', {'form': AttendeeForm()})
    
    if request.method == 'POST':
        form = AttendeeForm(request.POST)
        if form.is_valid():
            try:
                # Crear y guardar el asistente
                attendee = form.save(commit=False)
                attendee.registered_at_event = True
                attendee.arrived = True
                attendee.arrival_time = timezone.now()
                attendee.event = active_event
                attendee.save()
                
                # Enviar correo de bienvenida (no fallar si hay error)
                try:
                    send_welcome_email(attendee)
                    email_status = "Se enviará un correo de bienvenida."
                except Exception as email_error:
                    print(f"Error enviando correo: {email_error}")
                    email_status = "El registro fue exitoso, pero hubo un problema enviando el correo."
                
                # Mostrar mensaje de éxito
                messages.success(request, f"¡Registro exitoso! {attendee.name} {attendee.last_name} ha sido registrado y marcado como presente. {email_status}")
                
                return redirect('register')
                
            except Exception as e:
                print(f"Error en el registro: {str(e)}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Hubo un problema con el registro: {str(e)}")
        else:
            # Procesar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = AttendeeForm()
    
    return render(request, 'ponchapr_app/register.html', {
        'form': form,
        'active_event': active_event
    })

@staff_member_required
def check_in_attendee(request, attendee_id):
    attendee = Attendee.objects.get(id=attendee_id)
    if not attendee.arrived:
        attendee.arrived = True
        attendee.arrival_time = timezone.now()
        attendee.save()
        messages.success(request, f"{attendee.name} {attendee.last_name} ha llegado!")
    else:
        messages.warning(request, f"{attendee.name} {attendee.last_name} ya ha sido registrado!")
    return redirect('admin:ponchapr_app_attendee_changelist')

@staff_member_required
def dashboard_view(request):
    event_id = request.GET.get('event_id')
    
    if event_id:
        selected_event = get_object_or_404(Event, id=event_id)
    else:
        selected_event = Event.objects.filter(is_active=True).first()
    
    # Get all events for the selector
    all_events = Event.objects.all().order_by('-date')

    # Basic statistics - filter by selected event
    if selected_event:
        total_attendees = Attendee.objects.filter(event=selected_event).count()
        arrived_attendees = Attendee.objects.filter(event=selected_event, arrived=True).count()
        checked_out_attendees = Attendee.objects.filter(event=selected_event, checked_out=True).count()
        pre_registered_count = Attendee.objects.filter(event=selected_event, pre_registered=True).count()
        front_desk_count = Attendee.objects.filter(event=selected_event, registered_at_event=True).count()
    else:
        total_attendees = Attendee.objects.count()
        arrived_attendees = Attendee.objects.filter(arrived=True).count()
        checked_out_attendees = Attendee.objects.filter(checked_out=True).count()
        pre_registered_count = Attendee.objects.filter(pre_registered=True).count()
        front_desk_count = Attendee.objects.filter(registered_at_event=True).count()
    
    # Calculate attendance percentages
    expected_attendees = 200
    if total_attendees > 0:
        arrival_percentage = int((arrived_attendees / total_attendees) * 100)
    else:
        arrival_percentage = 0
    
    # Pre-registered percentage
    pre_registered_percentage = 0
    if total_attendees > 0:
        pre_registered_percentage = int((pre_registered_count / total_attendees) * 100)
    
    # Get all attendees for the data table - ordered by creation date (most recent first)
    attendees = Attendee.objects.filter(event=selected_event).order_by('-created_at') if selected_event else []
    
    # Get organization statistics for the dashboard
    organization_stats = {}
    if selected_event:
        org_data = (
            Attendee.objects.filter(event=selected_event)
            .exclude(organization__isnull=True)
            .exclude(organization='')
            .values('organization')
            .annotate(
                total=Count('id'),
                pre_registered=Count('id', filter=Q(pre_registered=True)),
                registered_at_event=Count('id', filter=Q(registered_at_event=True))
            )
            .order_by('-total')[:10]  # Top 10 organizations
        )
        organization_stats = list(org_data)
    
    # Get registration timeline (last 7 days)
    from datetime import timedelta
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    daily_registrations = []
    if selected_event:
        daily_data = (
            Attendee.objects.filter(
                event=selected_event,
                created_at__range=(start_date, end_date)
            )
            .extra(select={'day': 'date(created_at)'})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        daily_registrations = list(daily_data)
    
    context = {
        'total_attendees': total_attendees,
        'arrived_attendees': arrived_attendees,
        'checked_out_attendees': checked_out_attendees,
        'arrival_percentage': arrival_percentage,
        'pre_registered_count': pre_registered_count,
        'pre_registered_percentage': pre_registered_percentage,
        'front_desk_count': front_desk_count,
        'expected_attendees': expected_attendees,
        'selected_event': selected_event,
        'all_events': all_events,
        'attendees': attendees,
        'organization_stats': organization_stats,
        'daily_registrations': daily_registrations,
    }
    
    return render(request, "ponchapr_app/index.html", context)

def verify_checkin_qr_code(request):
    if request.method == 'POST':
        try:
            # Check if the data is sent as JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                identifier = data.get('employee_id')  # The field name in your frontend
            else:
                # Handle form data
                identifier = request.POST.get('qr_code_id')
                
            print(f"Received identifier: {identifier}")
            
            try:
                # Try first by unique_id (new method)
                attendee = Attendee.objects.filter(unique_id=identifier).first()
                
                # If not found, try by qr_code_id (legacy method)
                if not attendee:
                    attendee = Attendee.objects.filter(qr_code_id=identifier).first()
                
                if not attendee:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid identifier: Attendee not found'
                    })
                    
                print(f"Found attendee: {attendee.name} {attendee.last_name}")
                
            except Exception as e:
                print(f"Error finding attendee: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error finding attendee: {str(e)}'
                })
            
            if not attendee.arrived:
                try:
                    attendee.arrived = True
                    attendee.arrival_time = timezone.now()
                    attendee.save()
                    print(f"Attendee {attendee.name} checked in successfully")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Attendee {attendee.name} {attendee.last_name} checked in successfully',
                        'attendee': {
                            'name': f"{attendee.name} {attendee.last_name}",
                            'email': attendee.email,
                            'arrived': attendee.arrived,
                            'arrival_time': attendee.arrival_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    })
                except Exception as e:
                    print(f"Error saving attendee check-in: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Error saving check-in: {str(e)}'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Attendee already checked in'
                })
                
        except Exception as e:
            print(f"Unexpected error in check-in process: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            })


def verify_checkout_qr_code(request):
    if request.method == 'POST':
        try:
            # Check if the data is sent as JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                identifier = data.get('employee_id')  # Match the field name used in your frontend
            else:
                # Handle form data
                identifier = request.POST.get('qr_code_id')
                
            print(f"Received identifier for checkout: {identifier}")
            
            if not identifier:
                return JsonResponse({
                    'success': False,
                    'message': 'No identifier received'
                })
                
            try:
                # Try first by unique_id (new method)
                attendee = Attendee.objects.filter(unique_id=identifier).first()
                
                # If not found, try by qr_code_id (legacy method)
                if not attendee:
                    attendee = Attendee.objects.filter(qr_code_id=identifier).first()
                
                if not attendee:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid identifier: Attendee not found'
                    })
                
                print(f"Found attendee for checkout: {attendee.name} {attendee.last_name}")
            except Exception as e:
                print(f"Error finding attendee for checkout: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error finding attendee: {str(e)}'
                })
            
            if attendee.arrived and not attendee.checked_out:
                try:
                    attendee.checked_out = True
                    attendee.checkout_time = timezone.now()
                    attendee.save()
                    print(f"Attendee {attendee.name} checked out successfully")
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Attendee {attendee.name} {attendee.last_name} checked out successfully',
                        'attendee': {
                            'name': f"{attendee.name} {attendee.last_name}",
                            'email': attendee.email,
                            'checkout_time': attendee.checkout_time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    })
                except Exception as e:
                    print(f"Error saving attendee check-out: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Error saving check-out: {str(e)}'
                    })
            elif not attendee.arrived:
                return JsonResponse({
                    'success': False,
                    'message': 'Attendee has not checked in yet'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Attendee has already checked out'
                })
                
        except Exception as e:
            print(f"Unexpected error in check-out process: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests are allowed'
        })
        
@staff_member_required
def checkin_qr_code_verify(request):
    return render(request, 'admin/ponchapr_app/checkin_qr_code_verify.html')

@staff_member_required
def checkout_qr_code_verify(request):
    return render(request, 'admin/ponchapr_app/checkout_qr_code_verify.html')


@staff_member_required
def dashboard_view(request):
    event_id = request.GET.get('event_id')
    
    if event_id:
        selected_event = get_object_or_404(Event, id=event_id)
    else:
        selected_event = Event.objects.filter(is_active=True).first()
    
    # Get all events for the selector
    all_events = Event.objects.all().order_by('-date')

    # Basic statistics - filter by selected event
    if selected_event:
        total_attendees = Attendee.objects.filter(event=selected_event).count()
        arrived_attendees = Attendee.objects.filter(event=selected_event, arrived=True).count()
        checked_out_attendees = Attendee.objects.filter(event=selected_event, checked_out=True).count()
        pre_registered_count = Attendee.objects.filter(event=selected_event, pre_registered=True).count()
        front_desk_count = Attendee.objects.filter(event=selected_event, registered_at_event=True).count()
    else:
        total_attendees = Attendee.objects.count()
        arrived_attendees = Attendee.objects.filter(arrived=True).count()
        checked_out_attendees = Attendee.objects.filter(checked_out=True).count()
        pre_registered_count = Attendee.objects.filter(pre_registered=True).count()
        front_desk_count = Attendee.objects.filter(registered_at_event=True).count()
    
    # Calculate attendance percentages
    expected_attendees = 200
    arrival_percentage = round((arrived_attendees / expected_attendees) * 100, 1) if expected_attendees > 0 else 0
    checkout_percentage = round((checked_out_attendees / expected_attendees) * 100, 1) if expected_attendees > 0 else 0

    if total_attendees > 0:
        arrival_percentage = int((arrived_attendees / total_attendees) * 100)
    else:
        arrival_percentage = 0
    
    # Pre-registered percentage
    pre_registered_percentage = 0
    if total_attendees > 0:
        pre_registered_percentage = int((pre_registered_count / total_attendees) * 100)
    
    # Get all attendees for the data table - ordered by creation date (most recent first)
    attendees = Attendee.objects.filter(event=selected_event).order_by('-created_at') if selected_event else []
    
    # Get organization statistics for the dashboard
    organization_stats = {}
    if selected_event:
        org_data = (
            Attendee.objects.filter(event=selected_event)
            .exclude(organization__isnull=True)
            .exclude(organization='')
            .values('organization')
            .annotate(
                total=Count('id'),
                arrived=Count('id', filter=Q(arrived=True)),
                checked_out=Count('id', filter=Q(checked_out=True))
            )
            .order_by('-total')[:10]  # Top 10 organizations
        )
        organization_stats = list(org_data)
    
    # Get registration timeline (last 7 days)
    from datetime import timedelta
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    daily_registrations = []
    if selected_event:
        daily_data = (
            Attendee.objects.filter(
                event=selected_event,
                created_at__range=(start_date, end_date)
            )
            .extra(select={'day': 'date(created_at)'})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        daily_registrations = list(daily_data)
    
    context = {
        'total_attendees': total_attendees,
        'arrived_attendees': arrived_attendees,
        'checked_out_attendees': checked_out_attendees,
        'arrival_percentage': arrival_percentage,
        'pre_registered_count': pre_registered_count,
        'pre_registered_percentage': pre_registered_percentage,
        'front_desk_count': front_desk_count,
        'checkout_percentage': checkout_percentage,
        'expected_attendees': expected_attendees,
        'selected_event': selected_event,
        'all_events': all_events,
        'attendees': attendees,
        'organization_stats': organization_stats,
        'daily_registrations': daily_registrations,
    }
    
    return render(request, "ponchapr_app/index.html", context)

def checkout_form(request):

    active_event = Event.objects.filter(is_active=True).first()
    
    if not active_event:
        messages.error(request, "No hay un evento activo configurado. Por favor, contacte al administrador.")
        return render(request, 'ponchapr_app/checkout.html')

    if request.method == 'POST':
        unique_id = request.POST.get('unique_id')
        if unique_id:
            try:
                # Buscar el asistente por unique_id
                attendee = Attendee.objects.filter(
                    unique_id=unique_id,
                    event=active_event
                ).first()                

                if not attendee:
                    messages.error(request, "No se encontró ningún asistente con ese código de identificación.")
                    return render(request, 'ponchapr_app/checkout.html')
                
                if not attendee.arrived:
                    messages.warning(request, f"{attendee.name} {attendee.last_name} no ha registrado su llegada todavía.")
                    return render(request, 'ponchapr_app/checkout.html')
                
                if attendee.checked_out:
                    messages.warning(request, f"{attendee.name} {attendee.last_name} ya ha realizado el check-out.")
                    return render(request, 'ponchapr_app/checkout.html')
                
                # Realizar el check-out
                attendee.checked_out = True
                attendee.checkout_time = timezone.now()
                attendee.save()
                
                messages.success(request, f"¡Check-out exitoso para {attendee.name} {attendee.last_name}!")
                return render(request, 'ponchapr_app/checkout.html')
                
            except Exception as e:
                messages.error(request, f"Error al procesar el check-out: {str(e)}")
                return render(request, 'ponchapr_app/checkout.html')
        else:
            messages.error(request, "Por favor, ingrese un código de identificación.")
    
    return render(request, 'ponchapr_app/checkout.html')

def terms_view(request):
    return render(request,'ponchapr_app/terms.html')

@login_required
def generate_report(request):
    """
    Generate a PDF report of the specified event statistics and attendee list
    """
    try:
        # Get the event ID from query parameters
        event_id = request.GET.get('event_id')
        
        # If an event ID is provided, get that specific event
        if event_id:
            event = get_object_or_404(Event, id=event_id)
        else:
            # Otherwise, default to the active event
            event = Event.objects.filter(is_active=True).first()
            
        if not event:
            messages.error(request, "No se encontró un evento para generar el reporte. Seleccione un evento o active uno.")
            return redirect('dashboard')
        
        # Get statistics filtered by the selected event
        total_attendees = Attendee.objects.filter(event=event).count()
        arrived_attendees = Attendee.objects.filter(event=event, arrived=True).count()
        checked_out_attendees = Attendee.objects.filter(event=event, checked_out=True).count()
        
        # Calculate attendance percentages
        arrival_percentage = 0
        if total_attendees > 0:
            arrival_percentage = int((arrived_attendees / total_attendees) * 100)
        
        # Get registration type counts for the selected event
        pre_registered_count = Attendee.objects.filter(event=event, pre_registered=True).count()
        front_desk_count = Attendee.objects.filter(event=event, registered_at_event=True).count()
        
        # Get all attendees for this event - order by organization and then by created_at
        attendees = Attendee.objects.filter(event=event).order_by('organization', '-created_at')

        # Build the context dictionary
        context = {
            'event': event,
            'total_attendees': total_attendees,
            'arrived_attendees': arrived_attendees,
            'checked_out_attendees': checked_out_attendees,
            'arrival_percentage': arrival_percentage,
            'pre_registered_count': pre_registered_count,
            'front_desk_count': front_desk_count,
            'attendees': attendees,
            'generated_at': timezone.now(),
        }
        
        # Add any additional calculations or data needed for the report
        if attendees:
            # Calculate organization distribution
            organization_counts = {}
            organization_distribution = {}
            
            for attendee in attendees:
                org_name = attendee.organization if attendee.organization else 'Sin Organización'
                organization_counts[org_name] = organization_counts.get(org_name, 0) + 1
            
            # Calculate percentages
            total = len(attendees)
            for org, count in organization_counts.items():
                organization_distribution[org] = (count / total) * 100
                
            context['organization_distribution'] = organization_distribution
            context['organization_counts'] = organization_counts
            
            # Calculate registration distribution by date
            registration_by_date = {}
            for attendee in attendees:
                date_key = attendee.created_at.date()
                registration_by_date[date_key] = registration_by_date.get(date_key, 0) + 1
            
            context['registration_by_date'] = registration_by_date
            
            # Calculate average time spent at event (for checked-out attendees)
            from django.db.models import F, ExpressionWrapper, DurationField, Avg
            
            # Query for average time spent
            avg_time_result = Attendee.objects.filter(
                event=event,
                arrival_time__isnull=False,
                checkout_time__isnull=False
            ).annotate(
                time_spent=ExpressionWrapper(
                    F('checkout_time') - F('arrival_time'), 
                    output_field=DurationField()
                )
            ).aggregate(
                avg_time=Avg('time_spent')
            )
            
            if avg_time_result['avg_time']:
                avg_seconds = avg_time_result['avg_time'].total_seconds()
                avg_hours = int(avg_seconds // 3600)
                avg_minutes = int((avg_seconds % 3600) // 60)
                context['avg_time_spent'] = f"{avg_hours}h {avg_minutes}m"
            else:
                context['avg_time_spent'] = "N/A"
                
            # Get top organizations by participation
            top_organizations = (
                Attendee.objects.filter(event=event)
                .exclude(organization__isnull=True)
                .exclude(organization='')
                .values('organization')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            context['top_organizations'] = top_organizations
        
        # Create a response with the PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ADSEF_Event_Report_{event.name}_{event.date}.pdf"'
        
        # Render the template to a string
        template = get_template('ponchapr_app/event_report.html')
        html = template.render(context)
        
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Convert HTML to PDF in the buffer
        import xhtml2pdf.pisa as pisa
        pisa_status = pisa.CreatePDF(
            html,                   # HTML content
            dest=buffer,            # Output destination
            encoding='utf-8'
        )
        
        if pisa_status.err:
            return HttpResponse("Error generando el reporte PDF. Por favor intente nuevamente.", status=500)
        
        # Get the value of the buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Write the PDF to the response
        response.write(pdf)
        
        return response
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f"Ocurrió un error: {str(e)}", status=500)

def landing_page(request):
    """Muestra la página principal con instrucciones y botón para registro"""
    return render(request, 'ponchapr_app/instrucciones.html')


# Añadir esta nueva función a views.py

def get_offices(request):
    """
    Vista AJAX para obtener las oficinas de una región específica
    """
    region_id = request.GET.get('region_id')
    if region_id:
        try:
            # Obtener todas las oficinas de la región seleccionada
            offices = LocalOffice.objects.filter(region_id=region_id).order_by('office_name')
            
            # Formatear las oficinas para devolverlas como JSON
            offices_data = [{'id': office.id, 'name': office.office_name} for office in offices]
            
            return JsonResponse({'offices': offices_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'No se proporcionó un ID de región'}, status=400)


def custom_logout(request):
    """
    Logout personalizado que redirige al login
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('admin:login')  # Redirige al login del admin


# Añadir a ponchapr_app/views.py

from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

class CustomLoginView(auth_views.LoginView):
    """
    Vista de login que redirige según el tipo de usuario
    """
    template_name = 'admin/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        # Si es superusuario Y viene de la URL del admin, va al admin
        if user.is_superuser and '/admin/' in self.request.POST.get('next', ''):
            return '/admin/'
        
        # En todos los demás casos, staff users van al dashboard
        elif user.is_staff:
            return '/dashboard/'
        
        # Si no es staff, no tiene acceso
        else:
            return '/accounts/login/?error=no_permission'