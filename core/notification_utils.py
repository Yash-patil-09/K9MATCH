import logging
from core.models import Notification

logger = logging.getLogger(__name__)

def create_notification(recipient, title, message, notification_type='system', sender=None, link=None):
    """
    Creates an in-app notification for the recipient user.
    Handles graceful logging on failure without halting the request cycle.
    """
    if not recipient:
        return None
    try:
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link or '',
            is_read=False
        )
        return notification
    except Exception as e:
        logger.exception("Failed to create notification for user %s: %s", getattr(recipient, 'username', recipient), str(e))
        return None
