from django.contrib import admin
from django import forms

from .models import LikertScale, ParticipantResponse, Question, QuestionGroup, Survey
from accounts.models import User


class SurveyAdminForm(forms.ModelForm):
    """
    Custom form to filter researcher dropdown to only show staff users (researchers and superusers).
    """
    class Meta:
        model = Survey
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter researcher field to only show users with staff access
        self.fields['researcher'].queryset = User.objects.filter(is_staff=True)


class LikertScaleInline(admin.TabularInline):
    model = LikertScale
    extra = 1
    fields = ["name", "min_value", "max_value", "scale_labels"]
    verbose_name = "Likert Scale"
    verbose_name_plural = "Likert Scales"


class QuestionGroupInline(admin.TabularInline):
    model = QuestionGroup
    extra = 1
    fields = ["group_code", "title", "description", "order"]
    verbose_name = "Question Group"
    verbose_name_plural = "Question Groups"

    def get_queryset(self, request):
        """
        Order groups by their order field when displaying in admin.
        """
        qs = super().get_queryset(request)
        return qs.order_by("order")


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["question_type", "text", "order", "group", "question_number", "question_id", "likert_scale", "required", "reverse_coded", "options"]
    readonly_fields = ["question_id"]

    def get_queryset(self, request):
        """
        Order questions by their order field when displaying in admin.
        """
        qs = super().get_queryset(request)
        return qs.order_by("order")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter the likert_scale and group dropdowns to only show items belonging to this survey.
        """
        if db_field.name == "likert_scale":
            # Get the survey from the parent object being edited
            if hasattr(request, '_survey_obj'):
                kwargs["queryset"] = LikertScale.objects.filter(survey=request._survey_obj)
            else:
                kwargs["queryset"] = LikertScale.objects.none()
        elif db_field.name == "group":
            # Filter groups to only show groups belonging to this survey
            if hasattr(request, '_survey_obj'):
                kwargs["queryset"] = QuestionGroup.objects.filter(survey=request._survey_obj)
            else:
                kwargs["queryset"] = QuestionGroup.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    form = SurveyAdminForm
    list_display = ["title", "researcher", "domain", "is_active", "created_at"]
    list_filter = ["is_active", "domain", "created_at"]
    search_fields = ["title", "description", "researcher__email"]
    inlines = [LikertScaleInline, QuestionGroupInline, QuestionInline]
    actions = ["normalize_question_order"]
    fieldsets = [
        (
            "Survey Information",
            {"fields": ["title", "description", "researcher", "domain", "is_active", "randomize_questions"]},
        ),
        (
            "Default Likert Scale",
            {
                "fields": ["min_value", "max_value", "scale_labels"],
                "description": (
                    "Fallback scale used for any question that does not have a specific Likert Scale assigned. "
                    'Labels use JSON format: {"1": "Strongly Disagree", "2": "Disagree", "3": "Neutral", "4": "Agree", "5": "Strongly Agree"}'
                ),
            },
        ),
    ]

    def get_form(self, request, obj=None, **kwargs):
        # Store the survey object on the request so QuestionInline can filter scales
        request._survey_obj = obj
        return super().get_form(request, obj, **kwargs)

    @admin.action(description="Normalize question order (renumber 1, 2, 3...)")
    def normalize_question_order(self, request, queryset):
        """
        Admin action to normalize question order for selected surveys.
        Renumbers questions sequentially, removing gaps and duplicates.
        """
        count = 0
        for survey in queryset:
            survey.normalize_question_order()
            count += 1

        self.message_user(
            request,
            f"Successfully normalized question order for {count} survey(s).",
        )


@admin.register(ParticipantResponse)
class ParticipantResponseAdmin(admin.ModelAdmin):
    list_display = ["survey", "question", "participant", "answer", "test_badge", "created_at"]
    list_filter = ["survey", "is_test", "created_at"]
    search_fields = ["participant__email", "survey__title", "question__text", "answer"]
    readonly_fields = ["created_at", "updated_at"]

    def test_badge(self, obj):
        """Display a TEST badge for test submissions"""
        if obj.is_test:
            return "🧪 TEST"
        return ""
    test_badge.short_description = "Test Data"
