from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Event, EventRegistration
from .serializers import EventSerializer
from django.contrib.auth.models import User
from rest_framework import generics, permissions
from .serializers import UserSerializer
from django.utils.timezone import now
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import EventFilter
from .permissions import IsOrganizer
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from rest_framework.exceptions import NotFound
from .pagination import CustomEventPagination
from rest_framework import viewsets
from .serializers import UserSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    # Add filter backends for search, filtering, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['title', 'location']
    search_fields = ['title', 'location']
    ordering_fields = ['date', 'title']
    
    def get_queryset(self):
        # Filter for future events only
        return Event.objects.filter(date__gte=timezone.now())

class UpcomingEventListView(generics.ListAPIView):
    queryset = Event.objects.filter(date_time__gte=now())
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'location']
    ordering_fields = ['date_time', 'created_date']
    ordering = ['date_time']  # Default ordering by upcoming event date

# List and Create Events
class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Associate the event with the logged-in user (organizer)
        serializer.save(organizer=self.request.user)

# Retrieve, Update, Delete Events
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow users to manage only their own events
        return Event.objects.filter(organizer=self.request.user)


# Create User View (Sign Up)
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Retrieve, Update, Delete Users (Only for authenticated user)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure a user can only manage their own account
        return self.request.user

class RegisterForEventView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        event = Event.objects.get(id=event_id)
        user = request.user

        if event.is_registered(user):
            return Response({"detail": "You are already registered for this event."}, status=status.HTTP_400_BAD_REQUEST)

        if not event.has_space():
            return Response({"detail": "Event is fully booked. Consider joining the waitlist."}, status=status.HTTP_400_BAD_REQUEST)

        # Register user for the event
        event.attendees.add(user)
        EventRegistration.objects.create(event=event, user=user)
        return Response({"detail": "Successfully registered for the event."}, status=status.HTTP_200_OK)

class JoinWaitlistView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        event = Event.objects.get(id=event_id)
        user = request.user

        if event.is_waitlisted(user):
            return Response({"detail": "You are already on the waitlist."}, status=status.HTTP_400_BAD_REQUEST)

        # Add the user to the waitlist
        event.waitlist.add(user)
        return Response({"detail": "Successfully joined the waitlist."}, status=status.HTTP_200_OK)
    
class CreateEventView(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically assign the current user as the organizer
        serializer.save(organizer=self.request.user)

class ManageEventView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizer]

class RegisterUserView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Allow non-authenticated users to register
    authentication_classes = []  # No authentication needed for registration

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        # Perform validation
        if not username or not email or not password:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # Create the user
        user = User.objects.create(username=username, email=email, password=make_password(password))

        # Create a token for the user
        token, _ = Token.objects.get_or_create(user=user)

        return Response({'token': token.key, 'username': user.username, 'email': user.email}, status=status.HTTP_201_CREATED)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        user = token.user
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })
    
class EventListView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Only authenticated users can create events
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['location', 'date_time']  # Enable filtering by location and date
    search_fields = ['title']  # Enable searching by event title
    pagination_class = CustomEventPagination  # Use custom pagination (optional)

    def get_queryset(self):
        # Only list events that are in the future
        queryset = Event.objects.filter(date_time__gte=timezone.now())
        
        # Search filters for title, location, and date range
        title = self.request.query_params.get('title')
        location = self.request.query_params.get('location')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if title:
            queryset = queryset.filter(title__icontains=title)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if start_date and end_date:
            queryset = queryset.filter(date_time__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        # Assign the current user as the organizer
        serializer.save(organizer=self.request.user)

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Only allow the organizer to update or delete their own events
        if self.request.method in ['PUT', 'DELETE']:
            self.permission_classes = [permissions.IsAuthenticated, IsOrganizer]
        return super(EventDetailView, self).get_permissions()

class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            event = Event.objects.get(pk=self.kwargs['pk'])
        except Event.DoesNotExist:
            raise NotFound(detail="Event not found.")
        return event
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]