import django_filters
from .models import Event
from django.utils.timezone import now

class EventFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    date_time = django_filters.DateFromToRangeFilter(field_name='date_time')

    class Meta:
        model = Event
        fields = ['title', 'location', 'date_time']
