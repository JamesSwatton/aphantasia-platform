from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django import forms
from .models import Domain, DataDownloadLog, Message
from accounts.models import User
from surveys.models import FeedbackSurvey, ExitSurvey, DemographicSurvey, Question, QuestionGroup, LikertScale


class FeedbackQuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["question_type", "text", "order", "question_id", "likert_scale", "required"]
    readonly_fields = ["question_id"]
    verbose_name = "Question"
    verbose_name_plural = "Questions (Likert and Free Text only)"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("order")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "likert_scale":
            if hasattr(request, '_feedback_survey_obj'):
                kwargs["queryset"] = LikertScale.objects.filter(survey=request._feedback_survey_obj)
            else:
                kwargs["queryset"] = LikertScale.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "question_type":
            kwargs["choices"] = [
                ("likert", "Likert Scale"),
                ("free_text", "Free Text"),
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


class FeedbackLikertScaleInline(admin.TabularInline):
    model = LikertScale
    extra = 1
    fields = ["name", "min_value", "max_value", "scale_labels"]
    verbose_name = "Likert Scale"
    verbose_name_plural = "Likert Scales"


class FeedbackSurveyAdminForm(forms.ModelForm):
    class Meta:
        model = FeedbackSurvey
        fields = ["title", "description", "researcher", "is_active", "show_after_n_surveys", "min_value", "max_value", "scale_labels"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["researcher"].queryset = User.objects.filter(is_staff=True)


@admin.register(FeedbackSurvey)
class FeedbackSurveyAdmin(admin.ModelAdmin):
    form = FeedbackSurveyAdminForm
    list_display = ["title", "researcher", "is_active", "show_after_n_surveys", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]
    inlines = [FeedbackLikertScaleInline, FeedbackQuestionInline]
    fieldsets = [
        (
            "Feedback Survey",
            {"fields": ["title", "description", "researcher", "is_active"]},
        ),
        (
            "Display Trigger",
            {
                "fields": ["show_after_n_surveys"],
                "description": "Show this form on the participant account page after they have completed this many regular surveys.",
            },
        ),
        (
            "Default Likert Scale",
            {
                "fields": ["min_value", "max_value", "scale_labels"],
                "description": 'Fallback scale for Likert questions. Labels use JSON: {"1": "Strongly Disagree", "5": "Strongly Agree"}',
            },
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_feedback=True)

    def get_form(self, request, obj=None, **kwargs):
        request._feedback_survey_obj = obj
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.is_feedback = True
        super().save_model(request, obj, form, change)


class ExitQuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["question_type", "text", "order", "question_id", "likert_scale", "required"]
    readonly_fields = ["question_id"]
    verbose_name = "Question"
    verbose_name_plural = "Questions (Likert and Free Text only)"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("order")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "likert_scale":
            if hasattr(request, '_exit_survey_obj'):
                kwargs["queryset"] = LikertScale.objects.filter(survey=request._exit_survey_obj)
            else:
                kwargs["queryset"] = LikertScale.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "question_type":
            kwargs["choices"] = [
                ("likert", "Likert Scale"),
                ("free_text", "Free Text"),
            ]
        return super().formfield_for_choice_field(db_field, request, **kwargs)


class ExitLikertScaleInline(admin.TabularInline):
    model = LikertScale
    extra = 1
    fields = ["name", "min_value", "max_value", "scale_labels"]
    verbose_name = "Likert Scale"
    verbose_name_plural = "Likert Scales"


class ExitSurveyAdminForm(forms.ModelForm):
    class Meta:
        model = ExitSurvey
        fields = ["title", "description", "researcher", "is_active", "min_value", "max_value", "scale_labels"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["researcher"].queryset = User.objects.filter(is_staff=True)


@admin.register(ExitSurvey)
class ExitSurveyAdmin(admin.ModelAdmin):
    form = ExitSurveyAdminForm
    list_display = ["title", "researcher", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]
    inlines = [ExitLikertScaleInline, ExitQuestionInline]
    fieldsets = [
        (
            "Exit Survey",
            {"fields": ["title", "description", "researcher", "is_active"]},
        ),
        (
            "Default Likert Scale",
            {
                "fields": ["min_value", "max_value", "scale_labels"],
                "description": 'Fallback scale for Likert questions. Labels use JSON: {"1": "Strongly Disagree", "5": "Strongly Agree"}',
            },
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_exit_survey=True)

    def get_form(self, request, obj=None, **kwargs):
        request._exit_survey_obj = obj
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.is_exit_survey = True
        super().save_model(request, obj, form, change)


class DemographicLikertScaleInline(admin.TabularInline):
    model = LikertScale
    extra = 1
    fields = ["name", "min_value", "max_value", "scale_labels"]
    verbose_name = "Likert Scale"
    verbose_name_plural = "Likert Scales"


class DemographicQuestionGroupInline(admin.TabularInline):
    model = QuestionGroup
    extra = 1
    fields = ["title", "show_title", "order"]
    verbose_name = "Question Group"
    verbose_name_plural = "Question Groups"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("order")


class DemographicQuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["question_type", "text", "order", "group", "question_id", "likert_scale", "required", "options"]
    readonly_fields = ["question_id"]

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("order")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "likert_scale":
            if hasattr(request, '_demographic_survey_obj'):
                kwargs["queryset"] = LikertScale.objects.filter(survey=request._demographic_survey_obj)
            else:
                kwargs["queryset"] = LikertScale.objects.none()
        elif db_field.name == "group":
            if hasattr(request, '_demographic_survey_obj'):
                kwargs["queryset"] = QuestionGroup.objects.filter(survey=request._demographic_survey_obj)
            else:
                kwargs["queryset"] = QuestionGroup.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DemographicSurveyAdminForm(forms.ModelForm):
    class Meta:
        model = DemographicSurvey
        fields = ["title", "description", "instructions", "researcher", "is_active", "randomize_questions", "min_value", "max_value", "scale_labels"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["researcher"].queryset = User.objects.filter(is_staff=True)


@admin.register(DemographicSurvey)
class DemographicSurveyAdmin(admin.ModelAdmin):
    form = DemographicSurveyAdminForm
    list_display = ["title", "researcher", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]
    inlines = [DemographicLikertScaleInline, DemographicQuestionGroupInline, DemographicQuestionInline]
    fieldsets = [
        (
            "Demographic Survey",
            {
                "fields": ["title", "description", "instructions", "researcher", "is_active", "randomize_questions"],
                "description": "Participants must complete this survey before any other surveys or tasks become accessible.",
            },
        ),
        (
            "Default Likert Scale",
            {
                "fields": ["min_value", "max_value", "scale_labels"],
                "description": 'Fallback scale for Likert questions. Labels use JSON: {"1": "Strongly Disagree", "5": "Strongly Agree"}',
            },
        ),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_demographic=True)

    def get_form(self, request, obj=None, **kwargs):
        request._demographic_survey_obj = obj
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        obj.is_demographic = True
        super().save_model(request, obj, form, change)


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
    list_display = ['subject', 'sender_name', 'is_published', 'unlocks_with_survey', 'created_by', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['subject', 'sender_name', 'body']
    readonly_fields = ['created_by', 'created_at', 'updated_at']

    fieldsets = [
        ('Message Details', {
            'fields': ['subject', 'sender_name', 'body']
        }),
        ('Publishing', {
            'fields': ['is_published', 'unlocks_with_survey'],
            'description': (
                'Only published messages are visible to participants. '
                'Optionally tie this message to a Feedback Survey so it only appears once a '
                'participant has completed that survey\'s "Show after N surveys" threshold — '
                'useful for telegraphing that a feedback survey has become available.'
            ),
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
