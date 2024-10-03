from time import timezone
from rest_framework import serializers
from .models import Event
from django.contrib.auth.models import User
from rest_framework import serializers

class EventSerializer(serializers.ModelSerializer):
    available_slots = serializers.SerializerMethodField()
    organizer = serializers.ReadOnlyField(source= 'organizer.username')

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'date_time', 'location', 'organizer', 'capacity', 'created_date']
        read_only_fields = ['organizer', 'created_date']

    def get_available_slots(self, obj):
        return obj.capacity - obj.attendees.count()

    def validate_date_time(self, value):
        """Ensure the event date is in the future."""
        if value < timezone.now():
            raise serializers.ValidationError("The event date cannot be in the past.")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Use Django's create_user to handle password hashing
        user = User.objects.create_user(**validated_data )
        return user
