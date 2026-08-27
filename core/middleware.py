import base64
import binascii
import hmac

from django.conf import settings
from django.http import HttpResponse


class SiteBasicAuthMiddleware:
    """
    Gates the entire site behind one shared HTTP Basic Auth credential,
    ahead of Django's own login. Only active when SITE_BASIC_AUTH_USER and
    SITE_BASIC_AUTH_PASSWORD are both set — intended for locking down a
    testing-only deployment from public access, not a replacement for the
    app's own auth.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.username = getattr(settings, "SITE_BASIC_AUTH_USER", "")
        self.password = getattr(settings, "SITE_BASIC_AUTH_PASSWORD", "")
        self.enabled = bool(self.username and self.password)

    def __call__(self, request):
        if not self.enabled or self._is_authorized(request):
            return self.get_response(request)

        response = HttpResponse(status=401)
        response["WWW-Authenticate"] = 'Basic realm="Restricted"'
        return response

    def _is_authorized(self, request):
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8")
            username, password = decoded.split(":", 1)
        except (ValueError, binascii.Error, UnicodeDecodeError):
            return False
        return hmac.compare_digest(username, self.username) and hmac.compare_digest(
            password, self.password
        )
