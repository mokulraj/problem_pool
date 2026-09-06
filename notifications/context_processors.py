from .models import Notification


def notification_context(request):
    unread_notification_count = 0

    if request.user.is_authenticated:
        unread_notification_count = (
            Notification.objects
            .filter(
                recipient=request.user,
                is_read=False,
            )
            .count()
        )

    return {
        "unread_notification_count": unread_notification_count,
    }