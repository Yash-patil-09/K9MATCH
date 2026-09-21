from django.db.models import Q
from .models import MatchRequest, DogProfile, ChatMessage, Notification

def global_notifications(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        pending_matches_count = MatchRequest.objects.filter(
            receiver=request.user, 
            status='pending'
        ).count()
        admin_pending_dogs_count = 0
        if request.user.is_staff:
            admin_pending_dogs_count = DogProfile.objects.filter(approval_status='pending').count()

        # Unread incoming messages across all accepted matches
        user_matches = MatchRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            status='accepted'
        )
        unread_messages_count = ChatMessage.objects.filter(
            match__in=user_matches,
            is_read=False
        ).exclude(sender=request.user).count()

        # In-App Notifications
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = list(request.user.notifications.select_related('sender')[:8])

        return {
            'navbar_pending_matches_count': pending_matches_count,
            'admin_pending_dogs_count': admin_pending_dogs_count,
            'navbar_unread_messages_count': unread_messages_count,
            'unread_notifications_count': unread_notifications_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'navbar_pending_matches_count': 0,
        'admin_pending_dogs_count': 0,
        'navbar_unread_messages_count': 0,
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }