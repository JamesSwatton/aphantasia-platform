from django.contrib import admin
from .models import LabTask, TaskSubmission


@admin.register(LabTask)
class LabTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'researcher', 'domain', 'is_active', 'time_limit_minutes', 'created_at']
    list_filter = ['is_active', 'domain', 'created_at']
    search_fields = ['title', 'description', 'researcher__email']


@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ['task', 'participant', 'status', 'started_at', 'completed_at', 'time_spent_seconds']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['task__title', 'participant__email']
    readonly_fields = ['started_at', 'updated_at']
