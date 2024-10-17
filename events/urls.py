from django.urls import path, include
from .views import (
    EventListCreateView, EventDetailView, 
    UserCreateView, UserDetailView, 
    UpcomingEventListView, RegisterForEventView, JoinWaitlistView,
    CreateEventView, ManageEventView, RegisterUserView, CustomAuthToken,
    EventListView, EventDetailView, EventViewSet, UserViewSet
)

from rest_framework.routers import DefaultRouter
from .views import EventListCreateView
# Initialize the DefaultRouter and register viewsets
router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'users', UserViewSet, basename='user')

# Define URL patterns for the app
urlpatterns = [
    path('events/', EventListCreateView.as_view(), name='event-list-create'),
    path('events/<int:pk>/', EventDetailView.as_view(), name='event-detail'),
    path('users/', UserCreateView.as_view(), name='user-create'),
    path('users/me/', UserDetailView.as_view(), name='user-detail'),
    path('events/upcoming/', UpcomingEventListView.as_view(), name='upcoming-events'),
    path('events/<int:event_id>/register/', RegisterForEventView.as_view(), name='register-event'),
    path('events/<int:event_id>/waitlist/', JoinWaitlistView.as_view(), name='waitlist-event'),
    path('create-event/', CreateEventView.as_view(), name='create-event'),
    path('events/<int:pk>/manage/', ManageEventView.as_view(), name='manage-event'),
    path('api/register/', RegisterUserView.as_view(), name='register'),
    path('api/login/', CustomAuthToken.as_view(), name='login'),
    path('api/events/', EventListView.as_view(), name='event-list'),
    path('', include(router.urls)),  # Includes the router URLs for viewsets
    
]
