from .models import Notification


def create_notification(
    recipient,
    message,
    notification_type,
    actor=None,
    problem=None,
    solution=None,
    project=None,
):
    if recipient is None:
        return None

    if actor is not None and recipient.pk == actor.pk:
        return None

    return Notification.objects.create(
        recipient=recipient,
        message=message,
        notification_type=notification_type,
        related_problem=problem,
        related_solution=solution,
        related_project=project,
    )