from django.contrib import admin
from django.utils.html import format_html
from .models import LabTask, TaskSubmission


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
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
            'fields': ['is_active', 'time_limit_minutes', 'instructions']
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


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ['task', 'participant', 'status', 'started_at', 'completed_at', 'time_spent_seconds']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['task__title', 'participant__email']
    readonly_fields = ['started_at', 'updated_at']
