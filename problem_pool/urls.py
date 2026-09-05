from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "",
        include("accounts.urls")
    ),
    
    path(
    "",
    include("problems.urls")
),
    
    path(
    "",
    include("solutions.urls")
    ),
    
    path(
    "",
    include("comments.urls")
),
    
    path("", include("projects.urls")),
    
    path("", include("teams.urls")),
]


if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )