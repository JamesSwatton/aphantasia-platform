from django.db import models
from django.conf import settings
from core.models import Domain


class LabTask(models.Model):
    """
    Lab.js tasks uploaded by researchers for participants to complete.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lab_tasks'
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lab_tasks'
    )
    task_file = models.FileField(
        upload_to='lab_tasks/%Y/%m/',
        help_text="Upload lab.js task HTML file or archive"
    )
    is_active = models.BooleanField(default=True)
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional time limit for task completion"
    )
    instructions = models.TextField(
        blank=True,
        help_text="Instructions shown to participants before starting the task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lab Task'
        verbose_name_plural = 'Lab Tasks'

    def __str__(self):
        return self.title


class TaskSubmission(models.Model):
    """
    Records of participants' lab task submissions and results.
    """
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    task = models.ForeignKey(
        LabTask,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_submissions'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='started'
    )
    results_data = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON data from lab.js task results"
    )
    time_spent_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total time spent on the task in seconds"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Task Submission'
        verbose_name_plural = 'Task Submissions'
        unique_together = ['task', 'participant']

    def __str__(self):
        return f"{self.participant.email} - {self.task.title} ({self.status})"
