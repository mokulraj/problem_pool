from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [
    path(
        "notifications/",
        views.notification_list,
        name="list",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.mark_read,
        name="mark_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_read,
        name="mark_all_read",
    ),
]