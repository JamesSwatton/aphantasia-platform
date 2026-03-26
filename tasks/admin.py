import csv
from datetime import date

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.html import format_html
from django import forms
from .models import LabTask, TaskSubmission
from accounts.models import User
from core.models import DataDownloadLog


class LabTaskAdminForm(forms.ModelForm):
    """
    Custom form to filter researcher dropdown to only show staff users (researchers and superusers).
    """
    class Meta:
        model = LabTask
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter researcher field to only show users with staff access
        self.fields['researcher'].queryset = User.objects.filter(is_staff=True)


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    form = LabTaskAdminForm
    list_display = ['title', 'researcher', 'domain', 'is_active', 'unpacked_status', 'preview_link_display', 'created_at']
    list_filter = ['is_active', 'domain', 'created_at']
    search_fields = ['title', 'description', 'researcher__email']
    readonly_fields = ['task_slug', 'task_directory', 'created_at', 'updated_at', 'preview_link']

    fieldsets = [
        ('Task Information', {
            'fields': ['title', 'description', 'researcher', 'domain']
        }),
        ('Task File', {
            'fields': ['zip_file', 'task_slug', 'task_directory', 'preview_link'],
            'description': '''
                <strong>Upload Instructions:</strong><br>
                1. Export your lab.js experiment as a zip file<br>
                2. Make sure your task includes a completion screen that redirects to: <code>/tasks/${TASK_ID}/complete/</code><br>
                3. Upload the zip file here<br>
                <br>
                <a href="/static/LABJS_INTEGRATION.md" target="_blank" style="color: #3498db; font-weight: bold;">
                    📖 View Full Integration Guide
                </a> |
                <a href="https://github.com/your-repo/blob/main/LABJS_INTEGRATION.md" target="_blank" style="color: #3498db;">
                    View on GitHub
                </a>
            '''
        }),
        ('Settings', {
            'fields': ['is_active', 'time_limit_minutes', 'instructions', 'trial_sender_filter']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def unpacked_status(self, obj):
        """Show if task has been successfully unpacked."""
        if obj.task_directory:
            return format_html('<span style="color: green;">✓ Unpacked</span>')
        return format_html('<span style="color: orange;">⧗ Pending</span>')
    unpacked_status.short_description = 'Status'

    def preview_link(self, obj):
        """Show link to preview the task (for detail view)."""
        if obj.task_directory:
            url = obj.get_index_url()
            return format_html(
                '<a href="{}" target="_blank">Preview Task →</a>',
                url
            )
        return "Upload and save to generate preview link"
    preview_link.short_description = 'Preview'

    def preview_link_display(self, obj):
        """Show link to preview the task (for list view)."""
        if obj.task_directory:
            url = obj.get_index_url()
            return format_html(
                '<a href="{}" target="_blank">Preview →</a>',
                url
            )
        return format_html('<span style="color: #999;">—</span>')
    preview_link_display.short_description = 'Preview'

    def delete_queryset(self, request, queryset):
        """
        Override bulk delete to call delete() on each instance.
        This ensures file cleanup happens for each task.
        """
        for obj in queryset:
            obj.delete()

    def delete_model(self, request, obj):
        """
        Override single delete to ensure cleanup happens.
        """
        obj.delete()


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ['task', 'participant', 'status', 'is_test_badge', 'started_at', 'completed_at', 'time_spent_seconds', 'trial_count']
    list_filter = ['status', 'is_test', 'started_at', 'completed_at']
    search_fields = ['task__title', 'participant__email']
    readonly_fields = ['started_at', 'updated_at', 'trial_data_display', 'is_test_badge']
    actions = ['export_trial_data_csv', 'export_raw_data_csv']

    # Fields that are internal lab.js timing/rendering metadata, not useful to researchers
    LABJS_INTERNAL_FIELDS = {
        'sender_type', 'sender_id',
        'time_run', 'time_render', 'time_show', 'time_end', 'time_commit', 'time_switch',
        'url', 'meta',
    }

    # Fields to show first, in this order, if present
    PRIORITY_FIELDS = ['sender', 'timestamp', 'duration', 'response', 'correct', 'correctResponse', 'ended_on']

    fieldsets = [
        ('Submission Info', {
            'fields': ['task', 'participant', 'status', 'is_test', 'time_spent_seconds', 'started_at', 'completed_at', 'updated_at']
        }),
        ('Trial Data', {
            'fields': ['trial_data_display'],
            'description': 'Filtered to rows where the participant actively responded (ended_on = "response").'
        }),
        ('Raw Data', {
            'fields': ['results_data'],
            'classes': ['collapse'],
            'description': 'Complete unfiltered data from lab.js. Expand to inspect all rows.'
        }),
    ]

    def trial_count(self, obj):
        """Number of response rows recorded for this submission."""
        return len(obj.get_trial_data())
    trial_count.short_description = 'Trials'

    def is_test_badge(self, obj):
        """Visual indicator for test submissions."""
        if obj.is_test:
            return format_html(
                '<span style="background: #e67e22; color: white; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">TEST</span>'
            )
        return format_html('<span style="color: #999;">—</span>')
    is_test_badge.short_description = 'Test'

    def trial_data_display(self, obj):
        """Render get_trial_data() as a formatted HTML table for the admin detail view."""
        rows = obj.get_trial_data()

        if not rows:
            return format_html('<p style="color: #999;">No trial data recorded yet.</p>')

        # Build ordered column list: priority fields first, then any task-specific fields,
        # excluding internal lab.js metadata fields
        all_keys = []
        for row in rows:
            for key in row.keys():
                if key not in all_keys:
                    all_keys.append(key)

        priority = [f for f in self.PRIORITY_FIELDS if f in all_keys]
        extras = [f for f in all_keys if f not in self.PRIORITY_FIELDS and f not in self.LABJS_INTERNAL_FIELDS]
        columns = priority + extras

        # Build header row
        header_cells = ''.join(
            f'<th style="padding: 6px 12px; text-align: left; border-bottom: 2px solid #ddd; white-space: nowrap;">{col}</th>'
            for col in columns
        )
        header = f'<tr>{header_cells}</tr>'

        # Build data rows
        data_rows = []
        for i, row in enumerate(rows):
            bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
            cells = []
            for col in columns:
                value = row.get(col, '')
                # Colour-code the correct field
                if col == 'correct':
                    if value is True:
                        cell = '<td style="padding: 5px 12px; color: green; font-weight: bold;">True</td>'
                    elif value is False:
                        cell = '<td style="padding: 5px 12px; color: red; font-weight: bold;">False</td>'
                    else:
                        cell = f'<td style="padding: 5px 12px;">—</td>'
                else:
                    cell = f'<td style="padding: 5px 12px;">{value}</td>'
                cells.append(cell)
            data_rows.append(f'<tr style="background: {bg};">{"".join(cells)}</tr>')

        table = (
            f'<div style="overflow-x: auto;">'
            f'<p style="color: #666; margin-bottom: 8px;">{len(rows)} response row(s)</p>'
            f'<table style="border-collapse: collapse; font-size: 13px; width: 100%;">'
            f'<thead style="background: #f0f0f0;">{header}</thead>'
            f'<tbody>{"".join(data_rows)}</tbody>'
            f'</table>'
            f'</div>'
        )
        return format_html(table)
    trial_data_display.short_description = 'Trial Responses'

    def _make_filename(self, prefix, queryset=None, task_slug=None):
        """
        Build a consistent CSV filename.
        - For a single submission (detail view): uses the provided task_slug.
        - For a queryset (list action): uses the task slug if all submissions share
          the same task, otherwise 'multiple-tasks'.
        """
        today = date.today().isoformat()
        if task_slug:
            slug = task_slug
        else:
            task_slugs = queryset.values_list('task__task_slug', flat=True).distinct()
            slug = task_slugs[0] if task_slugs.count() == 1 else 'multiple-tasks'
        return f"{prefix}_{slug}_{today}.csv"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/export-trial-csv/',
                self.admin_site.admin_view(self.export_single_trial_csv),
                name='tasks_tasksubmission_export_trial_csv',
            ),
            path(
                '<int:pk>/export-raw-csv/',
                self.admin_site.admin_view(self.export_single_raw_csv),
                name='tasks_tasksubmission_export_raw_csv',
            ),
        ]
        return custom_urls + urls

    def export_single_trial_csv(self, request, pk):
        """Export filtered trial data for a single submission."""
        submission = get_object_or_404(TaskSubmission, pk=pk)
        response = HttpResponse(content_type='text/csv')
        filename = self._make_filename('trial_data', task_slug=submission.task.task_slug)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        trials = submission.get_trial_data()

        all_trial_keys = []
        for trial in trials:
            for key in trial.keys():
                if key not in all_trial_keys:
                    all_trial_keys.append(key)

        priority = [f for f in self.PRIORITY_FIELDS if f in all_trial_keys]
        extras = [f for f in all_trial_keys if f not in self.PRIORITY_FIELDS and f not in self.LABJS_INTERNAL_FIELDS]
        trial_columns = priority + extras

        meta_columns = ['participant_email', 'task_title', 'submission_status', 'is_test', 'time_spent_seconds', 'started_at', 'completed_at']

        writer = csv.DictWriter(response, fieldnames=meta_columns + trial_columns, extrasaction='ignore')
        writer.writeheader()

        meta = {
            'participant_email': submission.participant.email,
            'task_title': submission.task.title,
            'submission_status': submission.status,
            'is_test': submission.is_test,
            'time_spent_seconds': submission.time_spent_seconds,
            'started_at': submission.started_at.isoformat() if submission.started_at else '',
            'completed_at': submission.completed_at.isoformat() if submission.completed_at else '',
        }
        for trial in trials:
            row = {**meta, **{k: v for k, v in trial.items() if k in trial_columns}}
            writer.writerow(row)

        # Log the download
        DataDownloadLog.objects.create(
            researcher=request.user,
            download_type='task_results',
            object_id=submission.task.id,
            file_format='csv',
            participant_count=1  # Single submission
        )

        return response

    def export_single_raw_csv(self, request, pk):
        """Export complete unfiltered data for a single submission."""
        submission = get_object_or_404(TaskSubmission, pk=pk)
        response = HttpResponse(content_type='text/csv')
        filename = self._make_filename('raw_data', task_slug=submission.task.task_slug)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        raw_rows = submission.results_data or []

        all_keys = []
        for row in raw_rows:
            for key in row.keys():
                if key not in all_keys:
                    all_keys.append(key)

        meta_columns = ['participant_email', 'task_title', 'submission_status', 'is_test', 'time_spent_seconds', 'started_at', 'completed_at']

        writer = csv.DictWriter(response, fieldnames=meta_columns + all_keys, extrasaction='ignore')
        writer.writeheader()

        meta = {
            'participant_email': submission.participant.email,
            'task_title': submission.task.title,
            'submission_status': submission.status,
            'is_test': submission.is_test,
            'time_spent_seconds': submission.time_spent_seconds,
            'started_at': submission.started_at.isoformat() if submission.started_at else '',
            'completed_at': submission.completed_at.isoformat() if submission.completed_at else '',
        }
        for row in raw_rows:
            writer.writerow({**meta, **row})

        # Log the download
        DataDownloadLog.objects.create(
            researcher=request.user,
            download_type='task_results',
            object_id=submission.task.id,
            file_format='csv',
            participant_count=1  # Single submission
        )

        return response

    @admin.action(description='Export trial data as CSV (filtered responses)')
    def export_trial_data_csv(self, request, queryset):
        """
        Export the filtered trial data (get_trial_data()) for selected submissions as CSV.
        Each row in the CSV corresponds to one trial response, with submission-level
        metadata (participant email, task title, is_test, status, time_spent_seconds)
        prepended as additional columns.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self._make_filename("trial_data", queryset=queryset)}"'

        # Gather all trial rows across selected submissions to determine full column set
        submission_rows = []
        all_trial_keys = []
        for submission in queryset:
            trials = submission.get_trial_data()
            submission_rows.append((submission, trials))
            for trial in trials:
                for key in trial.keys():
                    if key not in all_trial_keys:
                        all_trial_keys.append(key)

        # Order columns: priority trial fields first, then extras (excluding internal)
        priority = [f for f in self.PRIORITY_FIELDS if f in all_trial_keys]
        extras = [f for f in all_trial_keys if f not in self.PRIORITY_FIELDS and f not in self.LABJS_INTERNAL_FIELDS]
        trial_columns = priority + extras

        # Submission-level metadata columns prepended to every row
        meta_columns = ['participant_email', 'task_title', 'submission_status', 'is_test', 'time_spent_seconds', 'started_at', 'completed_at']

        writer = csv.DictWriter(response, fieldnames=meta_columns + trial_columns, extrasaction='ignore')
        writer.writeheader()

        for submission, trials in submission_rows:
            meta = {
                'participant_email': submission.participant.email,
                'task_title': submission.task.title,
                'submission_status': submission.status,
                'is_test': submission.is_test,
                'time_spent_seconds': submission.time_spent_seconds,
                'started_at': submission.started_at.isoformat() if submission.started_at else '',
                'completed_at': submission.completed_at.isoformat() if submission.completed_at else '',
            }
            if not trials:
                # Write a row with just metadata and empty trial columns
                writer.writerow(meta)
            else:
                for trial in trials:
                    row = {**meta, **{k: v for k, v in trial.items() if k in trial_columns}}
                    writer.writerow(row)

        # Log the download
        task_ids = queryset.values_list('task_id', flat=True).distinct()
        participant_ids = queryset.values_list('participant_id', flat=True).distinct()
        object_id = task_ids[0] if task_ids.count() == 1 else None

        DataDownloadLog.objects.create(
            researcher=request.user,
            download_type='task_results',
            object_id=object_id,
            file_format='csv',
            participant_count=participant_ids.count()
        )

        return response

    @admin.action(description='Export raw data as CSV (all lab.js rows)')
    def export_raw_data_csv(self, request, queryset):
        """
        Export the complete, unfiltered results_data for selected submissions as CSV.
        Every row from the lab.js datastore is included, with submission-level metadata prepended.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{self._make_filename("raw_data", queryset=queryset)}"'

        # Collect all raw rows to determine full column set
        submission_rows = []
        all_keys = []
        for submission in queryset:
            raw = submission.results_data or []
            submission_rows.append((submission, raw))
            for row in raw:
                for key in row.keys():
                    if key not in all_keys:
                        all_keys.append(key)

        meta_columns = ['participant_email', 'task_title', 'submission_status', 'is_test', 'time_spent_seconds', 'started_at', 'completed_at']

        writer = csv.DictWriter(response, fieldnames=meta_columns + all_keys, extrasaction='ignore')
        writer.writeheader()

        for submission, raw_rows in submission_rows:
            meta = {
                'participant_email': submission.participant.email,
                'task_title': submission.task.title,
                'submission_status': submission.status,
                'is_test': submission.is_test,
                'time_spent_seconds': submission.time_spent_seconds,
                'started_at': submission.started_at.isoformat() if submission.started_at else '',
                'completed_at': submission.completed_at.isoformat() if submission.completed_at else '',
            }
            if not raw_rows:
                writer.writerow(meta)
            else:
                for row in raw_rows:
                    writer.writerow({**meta, **row})

        # Log the download
        task_ids = queryset.values_list('task_id', flat=True).distinct()
        participant_ids = queryset.values_list('participant_id', flat=True).distinct()
        object_id = task_ids[0] if task_ids.count() == 1 else None

        DataDownloadLog.objects.create(
            researcher=request.user,
            download_type='task_results',
            object_id=object_id,
            file_format='csv',
            participant_count=participant_ids.count()
        )

        return response
