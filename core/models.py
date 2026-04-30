from django.db import models
from django.conf import settings


class Domain(models.Model):
    """
    Research domains or categories (e.g., Cognitive Psychology, Aphantasia, etc.)
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'

    def __str__(self):
        return self.name


class Researcher(models.Model):
    """
    Extended profile for users with researcher privileges.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='researcher_profile'
    )
    institution = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    domains = models.ManyToManyField(Domain, related_name='researchers', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__email']
        verbose_name = 'Researcher'
        verbose_name_plural = 'Researchers'

    def __str__(self):
        return f"{self.user.email} - {self.institution}"


class Participant(models.Model):
    """
    Extended profile for participants in research studies.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='participant_profile'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=50,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('non_binary', 'Non-binary'),
            ('prefer_not_to_say', 'Prefer not to say'),
            ('other', 'Other'),
        ],
        blank=True
    )
    country = models.CharField(max_length=100, blank=True)
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Participant'
        verbose_name_plural = 'Participants'

    def __str__(self):
        return f"{self.user.email}"


class DataDownloadLog(models.Model):
    """
    Logs when researchers download participant data for compliance and auditing.
    """
    researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='download_logs'
    )
    download_type = models.CharField(
        max_length=50,
        choices=[
            ('survey_responses', 'Survey Responses'),
            ('task_results', 'Task Results'),
            ('all_data', 'All Participant Data'),
        ]
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of specific survey or task, if applicable"
    )
    file_format = models.CharField(
        max_length=20,
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('excel', 'Excel'),
        ]
    )
    participant_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of participants included in download"
    )
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-downloaded_at']
        verbose_name = 'Data Download Log'
        verbose_name_plural = 'Data Download Logs'

    def __str__(self):
        return f"{self.researcher.email} - {self.download_type} ({self.downloaded_at.strftime('%Y-%m-%d %H:%M')})"


class Message(models.Model):
    """
    Messages from researchers to participants.
    Displayed in the participant messages page.
    """
    subject = models.CharField(
        max_length=200,
        help_text="Message subject line"
    )
    sender_name = models.CharField(
        max_length=200,
        help_text="Name of sender (e.g., 'Dr Bérengère Digard' or 'The Eye\'s Mind research team')"
    )
    body = models.TextField(
        help_text="Message content. Supports basic HTML: <p>, <strong>, <em>, <a>, <h4>, <ul>, <li>"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_messages'
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Only published messages are visible to participants"
    )
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_messages',
        blank=True,
        help_text="Participants who have marked this message as read"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f"{self.subject} (by {self.sender_name})"
