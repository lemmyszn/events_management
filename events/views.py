from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils.timezone import now
from .models import Event, EventRegistration
from .serializers import EventSerializer, UserSerializer
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet
from .filters import EventFilter
from .permissions import IsOrganizer
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
from .pagination import CustomEventPagination
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Event List and Create View
class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['title', 'location']
    search_fields = ['title', 'location']
    ordering_fields = ['date_time', 'title']
    ordering = ['date_time']

    def get_queryset(self):
        # Only list events that are in the future
        return Event.objects.filter(date_time__gte=timezone.now())

    def perform_create(self, serializer):
        # Automatically assign the current user as the organizer
        serializer.save(organizer=self.request.user)

# Detail View for Retrieve, Update, Delete
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

    def update(self, request, *args, **kwargs):
        # Check if the current user is the event's organizer
        event = self.get_object()
        if event.organizer != request.user:
            raise PermissionDenied(detail="You do not have permission to update this event.")
        
        # Perform the update if the user is the organizer
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Check if the current user is the event's organizer
        event = self.get_object()
        if event.organizer != request.user:
            raise PermissionDenied(detail="You do not have permission to delete this event.")
        
        # Perform the delete if the user is the organizer
        return super().destroy(request, *args, **kwargs)

# View for registering users for events
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

# View for creating users
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Handle additional user creation logic if needed
        serializer.save()

# View for handling user authentication (JWT token)
class CustomAuthToken(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
# User viewset for managing user details
class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Ensure users can only manage their own accounts
        return self.request.user

# User Detail View: Retrieve, Update, and Delete Users (Only for authenticated user)
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensure a user can only manage their own account
        return self.request.user

class UpcomingEventListView(generics.ListAPIView):
    queryset = Event.objects.filter(date_time__gte=now())  # Ensure you're using 'date_time'
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'location']
    ordering_fields = ['date_time', 'created_at']
    ordering = ['date_time']  # Default ordering by upcoming event date

class JoinWaitlistView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        event = Event.objects.get(id=event_id)
        user = request.user

        if event.is_waitlisted(user):
            return Response({"detail": "You are already on the waitlist."}, status=400)

        # Add the user to the waitlist
        event.waitlist.add(user)
        return Response({"detail": "Successfully joined the waitlist."}, status=200)

class CreateEventView(generics.createAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically assign the current user as the organizer of the event
        serializer.save(organizer=self.request.user)

class ManageEventView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]  # Only the organizer can manage the event

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Allow non-authenticated users to register

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

class EventListView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # Allow authenticated users to create events, others can only read
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['location', 'date_time']  # Filter by location and date
    search_fields = ['title']  # Search by event title
    ordering_fields = ['date_time']  # Order by event date
    pagination_class = CustomEventPagination  # Optional pagination

    def get_queryset(self):
        # Filter only future events
        queryset = Event.objects.filter(date_time__gte=timezone.now())
        
        # Apply filters for title, location, and date range
        title = self.request.query_params.get('title', None)
        location = self.request.query_params.get('location', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if title:
            queryset = queryset.filter(title__icontains=title)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if start_date and end_date:
            queryset = queryset.filter(date_time__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        # Automatically set the current user as the organizer
        serializer.save(organizer=self.request.user)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    # Add filter backends for search, filtering, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['title', 'location']
    search_fields = ['title', 'location']
    ordering_fields = ['date_time', 'title']
    
    def get_queryset(self):
        # Filter only future events
        return Event.objects.filter(date_time__gte=timezone.now())