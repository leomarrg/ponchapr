from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import modules, Dashboard
from registratepr_app.models import Attendee, Review
from django.db.models import Count
from django.db.models.functions import ExtractHour, ExtractMinute

class StatsModule(modules.DashboardModule):
    title = _('Statistics')
    template = 'admin/dashboard_modules/stats_module.html'
    
    def is_empty(self):
        return False
        
    def init_with_context(self, context):
        context.update({
            'total_attendees': Attendee.objects.count(),
            'arrived_attendees': Attendee.objects.filter(arrived=True).count(),
            'total_reviews': Review.objects.count(),
        })

class AttendeeChartModule(modules.DashboardModule):
    title = _('Attendee Arrivals')
    template = 'admin/dashboard_modules/attendees_chart.html'
    
    def __init__(self, **kwargs):
        super(AttendeeChartModule, self).__init__(**kwargs)
        self.id = 'attendee-chart'
    
    def is_empty(self):
        return False
        
    def init_with_context(self, context):
        try:
            # Debug: Print total events
            print("Total events:", Event.objects.count())
            
            # Get the current/most recent event
            current_event = Event.objects.filter(
                date__lte=timezone.now().date()
            ).order_by('-date').first()
            
            print("Current event:", current_event)
            
            if not current_event:
                print("No event found")
                self.children = []
                return
            
            # Get all attendees for debugging
            all_attendees = Attendee.objects.filter(event=current_event)
            print(f"Total attendees for event: {all_attendees.count()}")
            print(f"Arrived attendees: {all_attendees.filter(arrived=True).count()}")
            
            # Get attendees for this event within event hours
            attendees = (
                Attendee.objects
                .filter(
                    event=current_event,
                    arrived=True,
                    arrival_time__isnull=False
                )
                .annotate(
                    hour=ExtractHour('arrival_time'),
                    minute=ExtractMinute('arrival_time')
                )
                .values('hour', 'minute')
                .annotate(count=Count('id'))
                .order_by('hour', 'minute')
            )
            
            attendee_list = list(attendees)
            print("Attendees by hour:", attendee_list)
            
            self.children = attendee_list
            
        except Exception as e:
            print(f"Error in AttendeeChartModule: {e}")
            import traceback
            print(traceback.format_exc())
            self.children = []

class CustomDashboard(Dashboard):
    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)
        
    def init_with_context(self, context):
        # Column 1
        stats_group = modules.Group(
            title=_('Statistics'),
            column=1,
            collapsible=True,
        )
        stats_group.children.append(StatsModule())
        self.children.append(stats_group)

        qr_group = modules.Group(
            title=_('Quick Actions'),
            column=1,
            collapsible=False,
        )
        qr_group.children.append(modules.LinkList(
            title='',
            children=[
                {
                    'title': _('Scan QR Codes'),
                    'url': '/qr-scan/',
                    'external': False,
                },
            ]
        ))
        self.children.append(qr_group)

        # Column 2
        chart_group = modules.Group(
            title=_('Charts'),
            column=2,
            collapsible=True,
        )
        # Changed this line to use AttendeeChartModule instead of StatsModule
        chart_group.children.append(AttendeeChartModule())  # <-- This was the key fix
        self.children.append(chart_group)

        # Column 3: Administration
        admin_group = modules.Group(
            title=_('Administration'),
            column=3,
            collapsible=True,
        )
        admin_group.children.extend([
            modules.ModelList(
                title=_('Models'),
                exclude=('django.contrib.*',),
            ),
            modules.ModelList(
                title=_('Security'),
                models=('django.contrib.auth.*',)
            ),
        ])
        self.children.append(admin_group)