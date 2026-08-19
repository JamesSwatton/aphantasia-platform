from django import forms
from allauth.account.forms import SignupForm


# Fallback consent text in case no consent form exists in the database
DEFAULT_CONSENT_TEXT = """
RESEARCH PARTICIPATION CONSENT FORM

Thank you for your interest in participating in our research study on aphantasia and related conditions.

PURPOSE OF THE STUDY:
This research aims to better understand the experiences of individuals with aphantasia and contribute to scientific knowledge in this area.

WHAT YOU WILL DO:
- Complete surveys about your experiences
- Participate in research tasks
- Your responses will be used for research purposes only

CONFIDENTIALITY:
- Your data will be kept confidential and secure
- Only aggregated, de-identified data may be published
- You can withdraw from the study at any time

VOLUNTARY PARTICIPATION:
Your participation is completely voluntary. You may choose to stop participating at any time without penalty.

By checking the box below and creating an account, you acknowledge that you have read and understood this consent form and agree to participate in this research.
"""


class ParticipantSignupForm(SignupForm):
    name = forms.CharField(
        required=False,
        max_length=150,
        label="Username",
    )
    consent = forms.BooleanField(
        required=True,
        label="I have read and agree to the research participation consent form",
        error_messages={
            'required': 'You must agree to the consent form to participate in this research.'
        }
    )

    def get_active_consent_form(self):
        """
        Get the currently active consent form from the database.
        Returns the default consent text if no active form exists.
        """
        from .models import ConsentForm
        try:
            consent_form = ConsentForm.objects.filter(is_active=True).first()
            if consent_form:
                return consent_form.content
        except Exception:
            # If there's any database error, use the default
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


