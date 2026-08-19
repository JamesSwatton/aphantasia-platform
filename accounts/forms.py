from django import forms
from allauth.account.forms import SignupForm


DEFAULT_CONSENT_TEXT = """
I confirm that I have read and understand the Participant Information Sheet for the above study.

I agree to take part in the above study.
"""


def extract_consent_items(content):
    """
    Pull out markdown list items (lines starting with '- ') from consent content.
    Continuation lines (non-blank lines not starting a new item) are joined
    onto the previous item, matching how markdown parsers handle wrapped text.
    Returns a list of plain-text label strings.
    """
    items = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('- '):
            label = stripped[2:].strip()
            if label:
                items.append(label)
        elif stripped and items:
            # Continuation of the previous item
            items[-1] = items[-1] + ' ' + stripped
    return items


class ParticipantSignupForm(SignupForm):
    name = forms.CharField(
        required=False,
        max_length=150,
        label="Username",
    )
    consent = forms.BooleanField(
        required=True,
        label="I have read and agree to the research participation consent form",
        error_messages={'required': 'You must agree to the consent form to participate in this research.'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        items = extract_consent_items(self.get_active_consent_form())
        for i, label in enumerate(items):
            self.fields[f'consent_{i}'] = forms.BooleanField(
                required=True,
                label=label,
                error_messages={'required': 'You must tick all boxes to participate.'},
            )

    def get_active_consent_form(self):
        from .models import ConsentForm
        try:
            consent_form = ConsentForm.objects.filter(is_active=True).first()
            if consent_form:
                return consent_form.content
        except Exception:
            pass
        return DEFAULT_CONSENT_TEXT

    def save(self, request):
        user = super().save(request)
        user.consent_text = self.get_active_consent_form()
        user.is_participant = True
        name = self.cleaned_data.get('name', '').strip()
        if name:
            parts = name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        user.save()
        return user


