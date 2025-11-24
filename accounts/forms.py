from django import forms
from allauth.account.forms import SignupForm
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


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
    """
    Custom signup form for participants that includes consent.
    """
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
        # Store the consent text that was presented to the user
        user.consent_text = self.get_active_consent_form()
        user.is_participant = True
        user.save()
        return user


class InviteResearcherForm(forms.Form):
    """
    Form for inviting a new researcher to join the platform.
    """
    email = forms.EmailField(
        label="Email Address",
        help_text="Enter the email address of the person you want to invite as a researcher.",
        widget=forms.EmailInput(attrs={'class': 'vTextField', 'placeholder': 'researcher@example.com'})
    )
    expires_in_days = forms.IntegerField(
        label="Expires In (Days)",
        initial=7,
        min_value=1,
        max_value=30,
        help_text="Number of days until the invitation expires (1-30 days).",
        widget=forms.NumberInput(attrs={'class': 'vIntegerField'})
    )

    def __init__(self, *args, invited_by=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invited_by = invited_by

    def clean_email(self):
        """
        Validate that the email is not already registered or already invited.
        """
        from .models import User, ResearcherInvitation
        email = self.cleaned_data['email']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")

        # Check if there's already a pending invitation
        pending_invitation = ResearcherInvitation.objects.filter(
            email=email,
            used=False,
            expires_at__gt=timezone.now()
        ).first()

        if pending_invitation:
            raise forms.ValidationError(
                f"A pending invitation already exists for this email. It expires on {pending_invitation.expires_at.strftime('%Y-%m-%d %H:%M')}."
            )

        return email

    def save(self, request):
        """
        Create the invitation and send the email.
        """
        from .models import ResearcherInvitation

        email = self.cleaned_data['email']
        expires_in_days = self.cleaned_data['expires_in_days']

        # Create the invitation
        invitation = ResearcherInvitation.objects.create(
            email=email,
            invited_by=self.invited_by,
            expires_at=timezone.now() + timedelta(days=expires_in_days)
        )

        # Build the invitation URL
        invitation_url = request.build_absolute_uri(
            reverse('accounts:accept_invitation', kwargs={'token': str(invitation.token)})
        )

        # Send the invitation email
        send_mail(
            subject='Invitation to Join as a Researcher - Aphantasia Research Platform',
            message=f"""Hello,

You have been invited by {self.invited_by.email} to join the Aphantasia Research Platform as a researcher.

As a researcher, you will have access to:
- Create and manage surveys
- Upload and manage lab.js experimental tasks
- View participant responses and data
- Access the admin panel for research management

To accept this invitation and create your researcher account, please click the link below:

{invitation_url}

This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}.

If you did not expect this invitation, you can safely ignore this email.

Best regards,
Aphantasia Research Platform Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
            recipient_list=[email],
            fail_silently=False,
        )

        return invitation


class ResearcherSignupForm(forms.Form):
    """
    Form for researchers to sign up using an invitation token.
    """
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Your password must be at least 8 characters long."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter the same password again for verification."
    )
    first_name = forms.CharField(
        label="First Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, invitation=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invitation = invitation
        if invitation:
            self.fields['email'].initial = invitation.email

    def clean_password2(self):
        """
        Validate that the two password fields match.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")

        return password2

    def clean(self):
        """
        Additional validation.
        """
        cleaned_data = super().clean()

        # Validate password strength
        password1 = cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            self.add_error('password1', "Password must be at least 8 characters long.")

        return cleaned_data

    def save(self):
        """
        Create the user account with researcher privileges.
        """
        from .models import User

        user = User.objects.create_user(
            username=self.cleaned_data['email'],  # Use email as username
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            is_researcher=True,
            is_participant=True,  # Also marked as participant for testing purposes
        )

        # Mark the invitation as used
        if self.invitation:
            self.invitation.mark_as_used()

        return user
