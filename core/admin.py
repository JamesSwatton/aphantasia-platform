from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from .models import Domain, DataDownloadLog, Message
from accounts.models import User


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']


class ResearcherFilter(SimpleListFilter):
    """Custom filter to show only researchers in the dropdown."""
    title = 'researcher'
    parameter_name = 'researcher'

    def lookups(self, request, model_admin):
        """Return only users who are researchers/staff."""
        researchers = User.objects.filter(is_staff=True).order_by('email')
        return [(r.id, r.email) for r in researchers]

    def queryset(self, request, queryset):
        """Filter the queryset by selected researcher."""
        if self.value():
            return queryset.filter(researcher_id=self.value())
        return queryset


@admin.register(DataDownloadLog)
class DataDownloadLogAdmin(admin.ModelAdmin):
    list_display = ['researcher', 'download_type', 'object_title', 'file_format', 'participant_count', 'downloaded_at']
    list_filter = ['download_type', 'file_format', 'downloaded_at', ResearcherFilter]
    search_fields = ['researcher__email']
    readonly_fields = ['researcher', 'download_type', 'object_id', 'file_format', 'participant_count', 'downloaded_at']

    def object_title(self, obj):
        """Display the title of the survey or task that was downloaded."""
        if not obj.object_id:
            return '—'

        if obj.download_type == 'survey_responses':
            from surveys.models import Survey
            try:
                survey = Survey.objects.get(id=obj.object_id)
                return survey.title
            except Survey.DoesNotExist:
                return f'Survey #{obj.object_id} (deleted)'
        elif obj.download_type == 'task_results':
            from tasks.models import LabTask
            try:
                task = LabTask.objects.get(id=obj.object_id)
                return task.title
            except LabTask.DoesNotExist:
                return f'Task #{obj.object_id} (deleted)'
        return '—'
    object_title.short_description = 'Survey/Task'

    def has_add_permission(self, request):
        """Prevent manual creation of download logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs."""
        return request.user.is_superuser


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender_name', 'is_published', 'created_by', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['subject', 'sender_name', 'body']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    fieldsets = [
        ('Message Details', {
            'fields': ['subject', 'sender_name', 'body']
        }),
        ('Publishing', {
            'fields': ['is_published'],
            'description': 'Only published messages are visible to participants.'
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def save_model(self, request, obj, form, change):
        """Automatically set created_by to the current user when creating a new message."""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
