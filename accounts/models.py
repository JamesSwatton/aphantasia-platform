from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class User(AbstractUser):
    """
    Custom user model with researcher and participant roles.
    """
    is_researcher = models.BooleanField(
        default=False,
        help_text="Designates whether the user has researcher privileges."
    )
    is_participant = models.BooleanField(
        default=True,
        help_text="Designates whether the user is a participant."
    )
    consent_text = models.TextField(
        blank=True,
        help_text="The consent form text that was presented to the user during registration"
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email or self.username


class ConsentForm(models.Model):
    """
    Stores consent form text that participants see during registration.
    Only the most recent active consent form is used for new registrations.
    """
    title = models.CharField(
        max_length=200,
        default="Research Participation Consent Form",
        help_text="Title of the consent form"
    )
    content = models.TextField(
        help_text="Full text of the consent form shown to participants during registration"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one consent form should be active at a time"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version identifier for this consent form (e.g., 'v1.0', '2024-01')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consent Form'
        verbose_name_plural = 'Consent Forms'

    def __str__(self):
        active_status = " (Active)" if self.is_active else ""
        return f"{self.title}{active_status} - {self.version or 'No version'}"

    def save(self, *args, **kwargs):
        """
        If this consent form is being set to active, deactivate all other consent forms.
        """
        if self.is_active:
            ConsentForm.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ResearcherInvitation(models.Model):
    """
    Stores invitations for new researchers to join the platform.
    Uses a unique token for secure, one-time registration.
    """
    email = models.EmailField(
        help_text="Email address of the person being invited"
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique invitation token"
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text="The researcher who sent this invitation"
    )
    expires_at = models.DateTimeField(
        help_text="When this invitation expires"
    )
    used = models.BooleanField(
        default=False,
        help_text="Whether this invitation has been used"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this invitation was used"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Researcher Invitation'
        verbose_name_plural = 'Researcher Invitations'

    def __str__(self):
        status = "Used" if self.used else ("Expired" if self.is_expired() else "Pending")
        return f"Invitation to {self.email} ({status})"

    def save(self, *args, **kwargs):
        """
        Set default expiration time if not provided (7 days from creation).
        """
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        """
        Check if this invitation has expired.
        """
        return timezone.now() > self.expires_at

    def is_valid(self):
        """
        Check if this invitation is valid (not used and not expired).
        """
        return not self.used and not self.is_expired()

    def mark_as_used(self):
        """
        Mark this invitation as used.
        """
        self.used = True
        self.used_at = timezone.now()
        self.save()
