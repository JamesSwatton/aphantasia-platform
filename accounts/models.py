from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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

    def get_survey_progress(self):
        """
        Calculate survey completion progress for this user.
        Returns: (completed_count, total_count, percentage)
        """
        from surveys.models import Survey, ParticipantResponse

        # Get all active surveys
        total_surveys = Survey.objects.filter(is_active=True).count()

        # Get surveys this user has completed (has at least one response)
        completed_surveys = ParticipantResponse.objects.filter(
            participant=self,
            is_test=False
        ).values('survey_id').distinct().count()

        # Calculate percentage
        percentage = int((completed_surveys / total_surveys * 100)) if total_surveys > 0 else 0

        return (completed_surveys, total_surveys, percentage)

    def get_task_progress(self):
        """
        Calculate task completion progress for this user.
        Returns: (completed_count, total_count, percentage)
        """
        from tasks.models import LabTask, TaskSubmission

        # Get all active tasks that have been unpacked
        total_tasks = LabTask.objects.filter(
            is_active=True,
            task_directory__isnull=False
        ).count()

        # Get tasks this user has completed
        completed_tasks = TaskSubmission.objects.filter(
            participant=self,
            status='completed',
            is_test=False
        ).count()

        # Calculate percentage
        percentage = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        return (completed_tasks, total_tasks, percentage)

    def get_overall_progress(self):
        """
        Calculate overall completion progress across surveys and tasks.
        Returns: percentage (0-100)
        """
        survey_completed, survey_total, _ = self.get_survey_progress()
        task_completed, task_total, _ = self.get_task_progress()

        total_items = survey_total + task_total
        completed_items = survey_completed + task_completed

        if total_items == 0:
            return 0

        return int((completed_items / total_items * 100))


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


class WithdrawalText(models.Model):
    """
    Stores the withdrawal information text shown to participants on their account page.
    Supports markdown formatting — content is rendered to HTML when displayed.
    Only one record should be active at a time.
    """
    content = models.TextField(
        help_text="Markdown-formatted text explaining the withdrawal process and consequences."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one withdrawal text should be active at a time."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Withdrawal Text'
        verbose_name_plural = 'Withdrawal Texts'

    def __str__(self):
        status = " (Active)" if self.is_active else ""
        return f"Withdrawal Text{status} — last updated {self.updated_at.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        if self.is_active:
            WithdrawalText.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class WithdrawalRecord(models.Model):
    """
    Anonymised record created when a participant deletes their account.
    No foreign keys to User — survives account deletion permanently.
    responses is a list of {question, answer} dicts snapshotted from the exit survey.
    """
    participant_id = models.CharField(
        max_length=50,
        help_text="Anonymised participant ID at time of withdrawal (e.g. PRH-2026-0042)"
    )
    withdrawn_at = models.DateTimeField(default=timezone.now)
    exit_survey_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Title of the exit survey completed, if any"
    )
    responses = models.JSONField(
        default=list,
        help_text="List of {question, answer} dicts from the exit survey"
    )

    class Meta:
        ordering = ['-withdrawn_at']
        verbose_name = 'Withdrawal Record'
        verbose_name_plural = 'Withdrawal Records'

    def __str__(self):
        return f"{self.participant_id} — {self.withdrawn_at.strftime('%Y-%m-%d')}"


