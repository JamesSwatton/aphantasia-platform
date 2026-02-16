from django.contrib import admin
from django import forms

from .models import ParticipantResponse, Question, Survey
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


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["text", "order", "required", "reverse_coded"]

    def get_queryset(self, request):
        """
        Order questions by their order field when displaying in admin.
        """
        qs = super().get_queryset(request)
        return qs.order_by("order")


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    form = SurveyAdminForm
    list_display = ["title", "researcher", "domain", "is_active", "created_at"]
    list_filter = ["is_active", "domain", "created_at"]
    search_fields = ["title", "description", "researcher__email"]
    inlines = [QuestionInline]
    actions = ["normalize_question_order"]
    fieldsets = [
        (
            "Survey Information",
            {"fields": ["title", "description", "researcher", "domain", "is_active", "randomize_questions"]},
        ),
        (
            "Likert Scale Settings",
            {
                "fields": ["min_value", "max_value"],
                "description": "Set the minimum and maximum values for the Likert scale used in all questions (e.g., 1-5, 1-7, etc.)",
            },
        ),
        (
            "Scale Labels",
            {
                "fields": ["scale_labels"],
                "description": "Optional: Add labels for each scale value. Use JSON format with the value as key and label as value. "
                'Example: {"1": "Strongly Disagree", "2": "Disagree", "3": "Neutral", "4": "Agree", "5": "Strongly Agree"}',
                "classes": ["collapse"],
            },
        ),
    ]

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
    list_display = ["survey", "question", "participant", "answer", "created_at"]
    list_filter = ["survey", "created_at"]
    search_fields = ["participant__email", "survey__title", "question__text", "answer"]
    readonly_fields = ["created_at", "updated_at"]
