from django import template
from accounts.models import ConsentForm

register = template.Library()


@register.simple_tag
def get_active_consent_form():
    """
    Template tag to retrieve the active consent form.
    Returns the active ConsentForm object or None if no active form exists.
    """
    try:
        return ConsentForm.objects.filter(is_active=True).first()
    except Exception:
        return None
