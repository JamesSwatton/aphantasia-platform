"""
URL configuration for research_platform project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

# Customize admin site headers
admin.site.site_header = "Phantasia Research Administration"
admin.site.site_title = "Phantasia Research Admin"
admin.site.index_title = "Site Administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Custom accounts URLs (invitations, etc.) - must come before allauth
    path("accounts/", include("accounts.urls")),
    # Django allauth URLs
    path("accounts/", include("allauth.urls")),
    # App URLs
    path("", include("core.urls")),
    path("surveys/", include("surveys.urls")),
    path("tasks/", include("tasks.urls")),
    path("dashboard/", include("dashboard.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # No dedicated web server in front of gunicorn on Railway -- WhiteNoise only
    # serves STATIC_URL (collected at build time), not user-uploaded MEDIA_ROOT
    # content (e.g. unpacked lab.js tasks), so serve it directly via Django.
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    ]
