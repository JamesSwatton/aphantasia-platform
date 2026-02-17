from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import LabTask, TaskSubmission
from accounts.models import User


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
    list_display = ['title', 'researcher', 'domain', 'is_active', 'unpacked_status', 'created_at']
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
        """Show link to preview the task."""
        if obj.task_directory:
            url = obj.get_index_url()
            return format_html(
                '<a href="{}" target="_blank">Preview Task →</a>',
                url
            )
        return "Upload and save to generate preview link"
    preview_link.short_description = 'Preview'

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
