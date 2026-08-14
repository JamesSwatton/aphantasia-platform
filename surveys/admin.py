from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
import csv
from datetime import date

from .models import LikertScale, ParticipantResponse, Question, QuestionGroup, Survey
from accounts.models import User
from core.models import DataDownloadLog


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
    fields = ["title", "show_title", "result_label", "result_min", "result_max", "order"]
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
    fields = ["question_type", "text", "order", "group", "question_id", "likert_scale", "required", "reverse_coded", "scale_factor", "options", "controls_next_n_questions", "trigger_value"]
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
    list_display = ["title", "researcher", "domain", "is_active", "is_priority", "preview_link_display", "created_at"]
    list_filter = ["is_active", "is_priority", "domain", "created_at"]
    search_fields = ["title", "description", "researcher__email"]
    readonly_fields = ["preview_link_field"]
    inlines = [LikertScaleInline, QuestionGroupInline, QuestionInline]
    actions = ["normalize_question_order"]
    fieldsets = [
        (
            "Survey Information",
            {"fields": ["title", "description", "instructions", "researcher", "domain", "is_active", "is_priority", "randomize_questions", "preview_link_field"]},
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
        (
            "Results Display Range",
            {
                "fields": ["result_aggregation", "result_min", "result_max"],
                "description": (
                    "The range to which participant scores are mapped for display in charts. "
                    "Individual question groups can override this range. Leave blank if no mapping is needed."
                ),
            },
        ),
    ]

    def preview_link_display(self, obj):
        """Show link to preview the survey (for list view)."""
        url = reverse('surveys:survey_preview', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank">Preview →</a>',
            url
        )
    preview_link_display.short_description = 'Preview'

    def preview_link_field(self, obj):
        """Show link to preview the survey (for detail view)."""
        if obj.pk:
            url = reverse('surveys:survey_preview', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank">Preview Survey →</a>',
                url
            )
        return "Save survey first to generate preview link"
    preview_link_field.short_description = 'Preview'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_feedback=False, is_exit_survey=False, is_demographic=False)

    def get_form(self, request, obj=None, **kwargs):
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
    actions = ["export_responses_csv"]

    def test_badge(self, obj):
        """Display a TEST badge for test submissions"""
        if obj.is_test:
            return "🧪 TEST"
        return ""
    test_badge.short_description = "Test Data"

    @admin.action(description="Export responses as CSV (with full question metadata)")
    def export_responses_csv(self, request, queryset):
        """
        Export selected survey responses as CSV with complete question metadata.
        Each row contains one response with full question details.
        """
        response = HttpResponse(content_type='text/csv')

        # Generate filename
        today = date.today().isoformat()
        survey_titles = queryset.values_list('survey__title', flat=True).distinct()
        if survey_titles.count() == 1:
            survey_slug = survey_titles[0].lower().replace(' ', '-')[:30]
        else:
            survey_slug = 'multiple-surveys'
        response['Content-Disposition'] = f'attachment; filename="survey_responses_{survey_slug}_{today}.csv"'

        # Define CSV columns
        fieldnames = [
            # Participant info
            'participant_email',
            'participant_id',

            # Survey info
            'survey_title',
            'survey_id',

            # Question info
            'question_id',
            'question_text',
            'question_type',
            'question_order',
            'group_code',
            'group_title',

            # Question settings
            'required',
            'reverse_coded',
            'scale_factor',
            'min_value',
            'max_value',
            'likert_scale_name',

            # Response data
            'answer',
            'is_test',
            'created_at',
            'updated_at',
        ]

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        for response_obj in queryset.select_related(
            'participant', 'survey', 'question', 'question__group', 'question__likert_scale'
        ):
            q = response_obj.question

            # Get group info if question is in a group
            group_code = q.group.group_code if q.group else ''
            group_title = q.group.title if q.group else ''

            # Get scale info
            if q.question_type == 'likert':
                if q.likert_scale:
                    min_val = q.likert_scale.min_value
                    max_val = q.likert_scale.max_value
                    scale_name = q.likert_scale.name
                else:
                    min_val = q.survey.min_value
                    max_val = q.survey.max_value
                    scale_name = 'Survey Default'
            else:
                min_val = ''
                max_val = ''
                scale_name = ''

            row = {
                'participant_email': response_obj.participant.email,
                'participant_id': response_obj.participant.id,
                'survey_title': response_obj.survey.title,
                'survey_id': response_obj.survey.id,
                'question_id': q.question_id,
                'question_text': q.text,
                'question_type': q.question_type,
                'question_order': q.order,
                'group_code': group_code,
                'group_title': group_title,
                'required': q.required,
                'reverse_coded': q.reverse_coded if q.question_type == 'likert' else '',
                'scale_factor': q.scale_factor if q.question_type == 'likert' else '',
                'min_value': min_val,
                'max_value': max_val,
                'likert_scale_name': scale_name,
                'answer': response_obj.answer,
                'is_test': response_obj.is_test,
                'created_at': response_obj.created_at.isoformat(),
                'updated_at': response_obj.updated_at.isoformat(),
            }

            writer.writerow(row)

        # Log the download
        survey_ids = queryset.values_list('survey_id', flat=True).distinct()
        participant_ids = queryset.values_list('participant_id', flat=True).distinct()

        # Determine object_id (survey ID if single survey, None if multiple)
        object_id = survey_ids[0] if survey_ids.count() == 1 else None

        DataDownloadLog.objects.create(
            researcher=request.user,
            download_type='survey_responses',
            object_id=object_id,
            file_format='csv',
            participant_count=participant_ids.count()
        )

        return response
