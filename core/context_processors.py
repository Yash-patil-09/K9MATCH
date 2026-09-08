from .models import MatchRequest

def global_notifications(request):
    if request.user.is_authenticated:
        pending_matches_count = MatchRequest.objects.filter(
            receiver=request.user, 
            status='pending'
        ).count()
        return {'navbar_pending_matches_count': pending_matches_count}
    return {'navbar_pending_matches_count': 0}