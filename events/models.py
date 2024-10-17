from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.timezone import now




class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    capacity = models.IntegerField()
    created_date = models.DateTimeField(default=timezone.now)
    registered_users = models.ManyToManyField(User, related_name='registered_events', blank=True)
    waitlist = models.ManyToManyField(User, related_name='waitlist_events', blank=True)  # Optional waitlist feature
    



    def has_space(self):
        return self.attendees.count() < self.capacity

    def is_waitlisted(self, user):
        return user in self.waitlist.all()

    def is_registered(self, user):
        return user in self.attendees.all()

    def clean(self):
        """Ensure that the event date is in the future."""
        if self.date_time < timezone.now():
            raise ValidationError("Event date and time cannot be in the past.")

    def __str__(self):
        return self.title
    
    def is_past_event(self):
        return self.date_time < now()
    
    def can_manaage(self, user):
        return self.organizer == user
    
class EventRegistration(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')  # Ensure a user can only register for an event once

    def __str__(self):
        return f"{self.user.username} registered for {self.event.title}"

    def has_space(self):
        return self.attendees.count() < self.capacity
