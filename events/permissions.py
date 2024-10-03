from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsOrganizer(permissions.BasePermission):
    """
    Custom permission to only allow organizers of an event to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Object must have an organizer attribute (i.e., must be an event)
        return obj.organizer == request.user
    
class IsOrganizer(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Only allow the organizer of the event to edit or delete it
        return obj.organizer == request.user