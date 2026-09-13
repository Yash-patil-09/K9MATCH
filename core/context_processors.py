from .models import MatchRequest, DogProfile

def global_notifications(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        pending_matches_count = MatchRequest.objects.filter(
            receiver=request.user, 
            status='pending'
        ).count()
        admin_pending_dogs_count = 0
        if request.user.is_staff:
            admin_pending_dogs_count = DogProfile.objects.filter(approval_status='pending').count()
        return {
            'navbar_pending_matches_count': pending_matches_count,
            'admin_pending_dogs_count': admin_pending_dogs_count,
        }
    return {'navbar_pending_matches_count': 0, 'admin_pending_dogs_count': 0}