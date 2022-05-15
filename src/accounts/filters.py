import django_filters
from django.db.models import Q

from .models import User


class UserBasicFilter(django_filters.FilterSet):
    # query = django_filters.CharFilter(method='custom_filter')

    class Meta:
        model = User
        fields = {
            'id': ['exact'],
            'first_name': ['icontains'],
            'last_name': ['icontains'],
            'mobile': ['icontains'],
            'email': ['icontains'],
            'address': ['icontains'],
            'is_staff': ['exact'],
            'is_superuser': ['exact'],
            'is_active': ['exact'],
            'is_separated': ['exact']
        }

    def custom_filter(self, queryset, value):
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value) | Q(mobile__icontains=value) | Q(
                email__icontains=value) | Q(id__exact=value) | Q(
                address__icontains=value)
        )
