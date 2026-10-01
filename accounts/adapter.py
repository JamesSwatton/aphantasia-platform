import logging

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    def get_password_change_redirect_url(self, request):
        return reverse('accounts:account')

    def send_mail(self, template_prefix, email, context):
        """
        Same as the default implementation, except a delivery failure (e.g.
        the email provider rejecting the send) is logged and swallowed
        rather than propagating up and crashing the signup/login request.
        The account itself is still created either way.
        """
        try:
            super().send_mail(template_prefix, email, context)
        except Exception:
            logger.exception(
                "Failed to send '%s' email to %s", template_prefix, email
            )
