from django.contrib import admin
from .models import Domain, Researcher, Participant, Progress, DataDownloadLog


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'department', 'created_at']
    list_filter = ['institution', 'created_at']
    search_fields = ['user__email', 'institution', 'department']
    filter_horizontal = ['domains']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'country', 'consent_given', 'created_at']
    list_filter = ['gender', 'consent_given', 'country', 'created_at']
    search_fields = ['user__email', 'country']


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['participant', 'content_type', 'object_id', 'status', 'progress_percentage', 'last_accessed']
    list_filter = ['content_type', 'status', 'last_accessed']
    search_fields = ['participant__email']
    readonly_fields = ['created_at', 'last_accessed']


@admin.register(DataDownloadLog)
class DataDownloadLogAdmin(admin.ModelAdmin):
    list_display = ['researcher', 'download_type', 'file_format', 'participant_count', 'downloaded_at']
    list_filter = ['download_type', 'file_format', 'downloaded_at']
    search_fields = ['researcher__email']
    readonly_fields = ['downloaded_at']
