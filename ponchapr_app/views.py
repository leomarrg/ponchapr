from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .forms import AttendeeForm
from .models import Attendee, Event, Region, LocalOffice
from .utils import send_registration_email_async, schedule_registration_email
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

# Setup logging
logger = logging.getLogger(__name__)

def pre_register(request):
    if request.method == 'POST':
        form = AttendeeForm(request.POST)
        if form.is_valid():
            attendee = form.save(commit=False)
            attendee.pre_registered = True
            attendee.save()  # Save to generate unique_id
            
            # Add debugging
            print("Sending email with unique ID...")
            try:
                # Send the unique_id in the email
                send_registration_email_async(attendee, attendee.unique_id)
                print("Email sending initiated")
            except Exception as e:
                print(f"Error sending email: {e}")
                messages.error(request, f"Error sending email: {e}")
            
            messages.success(request, "Registro exitoso! El correo de confirmación será enviado en breve.")
            return render(request, 'ponchapr_app/pre_register.html', {'form': AttendeeForm()})
    else:
        form = AttendeeForm()
    
    return render(request, 'ponchapr_app/pre_register.html', {'form': form})
    

def front_desk_register(request):
    """Handle registrations that happen at the event (same day registrations)"""
    
    active_event = Event.objects.filter(is_active=True).first()

    if not active_event:
        messages.error(request, "No hay un evento activo configurado. Por favor, contacte al administrador.")
        # Redireccionar a una página adecuada o mostrar un formulario vacío
        return render(request, 'ponchapr_app/register.html', {'form': AttendeeForm()})
    
    if request.method == 'POST':
        form = AttendeeForm(request.POST)
        
        # Verificar si es una actualización de oficinas
        is_office_update = request.POST.get('is_office_update') == 'true'
        
        # Si hay errores en el formulario, asegurarse de que las oficinas se carguen
        if form.data.get('region'):
            try:
                region_id = int(form.data.get('region'))
                form.fields['office'].queryset = LocalOffice.objects.filter(region_id=region_id).order_by('office_name')
            except (ValueError, TypeError):
                pass
        
        # Si es solo una actualización de oficinas o hay errores, mostrar el formulario sin procesar
        if is_office_update or not form.is_valid():
            return render(request, 'ponchapr_app/register.html', {
                'form': form,
                'active_event': active_event
            })
        
        # Si el formulario es válido, procesar el registro
        try:
            # Crear y guardar el asistente
            attendee = form.save(commit=False)
            attendee.registered_at_event = True
            attendee.arrived = True
            attendee.arrival_time = timezone.now()
            attendee.event = active_event
            
            # Generar ID único
            import random
            import string
            temp_unique_id = ''.join(random.choices(string.digits, k=6))
            
            # Verificar que sea único
            while Attendee.objects.filter(unique_id=temp_unique_id).exists():
                temp_unique_id = ''.join(random.choices(string.digits, k=6))
            
            attendee.unique_id = temp_unique_id
            attendee.save()
            
            # Enviar email
            schedule_registration_email(attendee, attendee.unique_id)
            
            messages.success(request, f"¡Registro exitoso! Se enviará un correo de confirmación con su número de identificación.")
            return redirect('register')
            
        except Exception as e:
            print(f"Error en el registro: {str(e)}")
            messages.error(request, "Hubo un problema con el registro. Por favor intente nuevamente.")
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
def dashboard(request):
    # Basic statistics
    total_attendees = Attendee.objects.count()
    arrived_attendees = Attendee.objects.filter(arrived=True).count()
    checked_out_attendees = Attendee.objects.filter(checked_out=True).count()
    
    # Calculate attendance percentages
    arrival_percentage = 0
    if total_attendees > 0:
        arrival_percentage = int((arrived_attendees / total_attendees) * 100)
    
    # Get registration type counts for pie chart
    pre_registered_count = Attendee.objects.filter(pre_registered=True).count()
    front_desk_count = Attendee.objects.filter(registered_at_event=True).count()
    
    # Calculate pre-registration percentage
    pre_registered_percentage = 0
    if total_attendees > 0:
        pre_registered_percentage = int((pre_registered_count / total_attendees) * 100)
    
    # Get hourly check-in data for the area chart
    hourly_checkins = (
        Attendee.objects
        .filter(arrived=True, arrival_time__isnull=False)
        .annotate(hour=TruncHour('arrival_time'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    
    # Format chart data for JS
    chart_labels = []
    chart_data = []
    
    for entry in hourly_checkins:
        if entry['hour']:
            chart_labels.append(entry['hour'].strftime('%H:%M'))
            chart_data.append(entry['count'])
    
    # Get all attendees for the data table with related regions
    attendees = Attendee.objects.all().select_related('region').order_by('-created_at')
    
    context = {
        'total_attendees': total_attendees,
        'arrived_attendees': arrived_attendees,
        'checked_out_attendees': checked_out_attendees,
        'arrival_percentage': arrival_percentage,
        'pre_registered_count': pre_registered_count,
        'front_desk_count': front_desk_count,
        'pre_registered_percentage': pre_registered_percentage,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'attendees': attendees,
    }
    
    return render(request, 'admin/index.html', context)

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
    
    # Get all attendees for the data table with related regions
    attendees = Attendee.objects.filter(event=selected_event).select_related('region').order_by('-created_at') if selected_event else []
    
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
        
        # Get all attendees for this event - order by region name and then by created_at
        attendees = Attendee.objects.filter(event=event).select_related('region').order_by('region__name', '-created_at')

        # Get absolute path to the logo
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_dir, 'ponchapr_app', 'static', 'images', 'logo.png')

        # Build the context dictionary
        context = {
            'event': event,
            'total_attendees': total_attendees,
            'arrived_attendees': arrived_attendees,
            'checked_out_attendees': checked_out_attendees,
            'arrival_percentage': arrival_percentage,
            'pre_registered_count': pre_registered_count,
            'attendees': attendees,
            'generated_at': timezone.now(),
            'logo_path': logo_path
        }
        
        # Add any additional calculations or data needed for the report
        if attendees:
            # Calculate region distribution
            region_distribution = {}
            region_counts = {}
            for attendee in attendees:
                region_name = attendee.region.name if attendee.region else 'No Region'
                if region_name in region_distribution:
                    region_distribution[region_name] += 1
                    region_counts[region_name] += 1
                else:
                    region_distribution[region_name] = 1
                    region_counts[region_name] = 1
            
            # Calculate percentages
            total = len(attendees)
            for region in region_distribution:
                region_distribution[region] = (region_distribution[region] / total) * 100
                
            context['region_distribution'] = region_distribution
            context['region_counts'] = region_counts
            
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
        
        # Create a response with the PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="PonchaPR_Event_Report_{event.name}_{event.date}.pdf"'
        
        # Add a custom filter to access dictionary items by key in templates
        from django.template.defaulttags import register
        
        @register.filter
        def get_item(dictionary, key):
            return dictionary.get(key)
        
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
            return HttpResponse("Error generating PDF report. Please try again.", status=500)
        
        # Get the value of the buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        # Write the PDF to the response
        response.write(pdf)
        
        return response
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f"An error occurred: {str(e)}", status=500)

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