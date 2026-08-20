from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from core.models import Domain
import os
import zipfile
import shutil
from pathlib import Path


def validate_zip_file(file):
    """
    Validate that the uploaded file is a valid zip archive.
    """
    if not file.name.endswith('.zip'):
        raise ValidationError('Only .zip files are allowed.')

    # Check if it's a valid zip file
    try:
        zip_file = zipfile.ZipFile(file)
        # Check for index.html in the zip
        file_list = zip_file.namelist()
        if 'index.html' not in file_list:
            raise ValidationError('Zip file must contain an index.html file.')
        zip_file.close()
    except zipfile.BadZipFile:
        raise ValidationError('The uploaded file is not a valid zip archive.')


class LabTask(models.Model):
    """
    Lab.js tasks uploaded by researchers for participants to complete.
    Accepts zip files which are automatically unpacked and served.
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
    zip_file = models.FileField(
        upload_to='lab_tasks/zips/',
        help_text="Upload lab.js task as a .zip file (must contain index.html)",
        validators=[validate_zip_file],
        null=True,
        blank=True
    )
    task_slug = models.SlugField(
        max_length=250,
        blank=True,
        help_text="URL-safe identifier, generated from title"
    )
    task_directory = models.CharField(
        max_length=500,
        blank=True,
        help_text="Path to unpacked task directory"
    )
    trial_sender_filter = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Optional: comma-separated list of sender names to filter trial data to "
            "(e.g. 'Trial' or 'Trial, Stimulus'). "
            "If blank, all rows where ended_on='response' are included."
        )
    )
    is_active = models.BooleanField(default=True)
    is_priority = models.BooleanField(
        default=False,
        help_text="Mark this task as a priority. Priority tasks appear at the top of the list."
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional time limit for task completion"
    )
    instructions = models.TextField(
        blank=True,
        help_text="Instructions shown to participants before starting the task"
    )
    requires_min_window_size = models.BooleanField(
        default=False,
        help_text="Require the browser window to be at least the minimum size below before participants can start (e.g. for visual tasks that need enough screen space for usable data)."
    )
    min_window_width = models.PositiveIntegerField(
        default=1024,
        help_text="Minimum browser window width in pixels (only enforced if 'requires min window size' is checked)."
    )
    min_window_height = models.PositiveIntegerField(
        default=768,
        help_text="Minimum browser window height in pixels (only enforced if 'requires min window size' is checked)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_priority', '-created_at']
        verbose_name = 'Lab Task'
        verbose_name_plural = 'Lab Tasks'

    def __str__(self):
        return self.title

    def get_task_path(self):
        """
        Get the full filesystem path to the unpacked task directory.
        """
        if self.task_directory:
            return os.path.join(settings.MEDIA_ROOT, self.task_directory)
        return None

    def get_index_url(self):
        """
        Get the URL to the task's index.html file.
        """
        if self.task_directory:
            return os.path.join(settings.MEDIA_URL, self.task_directory, 'index.html')
        return None

    def unpack_zip(self):
        """
        Unpack the uploaded zip file to the task directory.
        Also replaces ${TASK_ID} placeholders in script.js with the actual task ID.
        """
        if not self.zip_file:
            return

        # Generate task directory name: {slug}-{id}
        task_dir_name = f"{self.task_slug}-{self.id}"
        task_dir_path = os.path.join('lab_tasks', 'unpacked', task_dir_name)
        full_path = os.path.join(settings.MEDIA_ROOT, task_dir_path)

        # Remove old directory if it exists
        if os.path.exists(full_path):
            shutil.rmtree(full_path)

        # Create directory and unpack
        os.makedirs(full_path, exist_ok=True)

        # Extract zip file
        with zipfile.ZipFile(self.zip_file.path, 'r') as zip_ref:
            zip_ref.extractall(full_path)

        # Replace ${TASK_ID} placeholder in script.js
        script_path = os.path.join(full_path, 'script.js')
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the placeholder
                content = content.replace('${TASK_ID}', str(self.id))

                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                # Log error but don't fail the upload
                print(f"Warning: Could not replace TASK_ID in script.js: {e}")

        # Store the relative path
        self.task_directory = task_dir_path

    def save(self, *args, **kwargs):
        """
        Override save to generate slug and unpack zip file.
        """
        # Generate slug from title if not set
        if not self.task_slug:
            self.task_slug = slugify(self.title)

        # Save first to get an ID
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Unpack zip file if it's a new task or zip file changed
        if self.zip_file:
            self.unpack_zip()
            # Save again to store the task_directory path
            if is_new or self.task_directory:
                # Use update to avoid recursion
                LabTask.objects.filter(pk=self.pk).update(
                    task_directory=self.task_directory
                )

    def delete(self, *args, **kwargs):
        """
        Override delete to clean up unpacked files.
        """
        # Delete unpacked directory
        if self.task_directory:
            full_path = os.path.join(settings.MEDIA_ROOT, self.task_directory)
            if os.path.exists(full_path):
                shutil.rmtree(full_path)

        # Delete zip file
        if self.zip_file:
            self.zip_file.delete(save=False)

        super().delete(*args, **kwargs)


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
    is_test = models.BooleanField(
        default=False,
        help_text="True if submitted by a researcher or staff member for testing purposes. Safe to delete after review."
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
    window_width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Browser window width (px) recorded when the participant started the task. Logged regardless of whether a minimum size was enforced, as a data-quality fallback."
    )
    window_height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Browser window height (px) recorded when the participant started the task."
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Task Submission'
        verbose_name_plural = 'Task Submissions'
        unique_together = ['task', 'participant']

    def get_trial_data(self):
        """
        Returns only the meaningful trial response rows from results_data,
        filtering out fixation screens, feedback screens, timeouts, etc.

        Base filter: ended_on == 'response' (participant actively responded).

        If the linked task has a trial_sender_filter set, additionally filters
        to only rows where sender matches one of the specified values.
        This is intentionally generic so it works across different lab.js task designs.
        """
        if not self.results_data:
            return []

        # Parse optional sender filter from the task
        sender_filter = None
        if self.task.trial_sender_filter:
            sender_filter = [s.strip() for s in self.task.trial_sender_filter.split(',') if s.strip()]

        return [
            entry for entry in self.results_data
            if entry.get('ended_on') == 'response'
            and (sender_filter is None or entry.get('sender') in sender_filter)
        ]

    def __str__(self):
        return f"{self.participant.email} - {self.task.title} ({self.status})"
