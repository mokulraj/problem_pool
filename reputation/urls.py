from django.urls import path

from . import views


app_name = "reputation"


urlpatterns = [
    path(
        "leaderboard/",
        views.leaderboard,
        name="leaderboard",
    ),
]