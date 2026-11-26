from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from allauth.account.models import EmailAddress
from .models import User, ConsentForm, WithdrawalText, WithdrawalRecord
import csv
from datetime import date

# Unregister allauth's EmailAddress model from admin
# We don't need manual management of email verification records
admin.site.unregister(EmailAddress)


class ParticipantIdSearchMixin:
    """
    Lets the admin search bar find participants by their PRH ID, which is
    computed rather than stored so can't go in search_fields.
    Set participant_lookup to the path from this model to the user's pk.
    """
    participant_lookup = 'pk'

    def get_search_results(self, request, queryset, search_term):
        results, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        pk = User.pk_from_participant_id(search_term)
        if pk is not None:
            results |= queryset.filter(**{self.participant_lookup: pk})
        return results, may_have_duplicates


class ParticipantDataAdminMixin(ParticipantIdSearchMixin):
    """
    For admins of participant data (responses, submissions): shows the
    participant as their PRH ID rather than their email, in the list column,
    the participant dropdown and search. Add 'participant_display' to list_display.
    """
    participant_lookup = 'participant_id'

    def participant_display(self, obj):
        return obj.participant.participant_id
    participant_display.short_description = 'Participant'
    participant_display.admin_order_field = 'participant'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'participant':
            field.label_from_instance = lambda user: user.participant_id
        return field


@admin.register(User)
class UserAdmin(ParticipantIdSearchMixin, BaseUserAdmin):
    """
    Admin configuration for custom User model.
    """
    list_display = ['participant_id_display', 'email', 'is_researcher', 'is_participant', 'survey_progress_display', 'task_progress_display', 'overall_progress_display', 'is_active', 'date_joined']
    list_filter = ['is_researcher', 'is_participant', 'is_active', 'date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role Information', {
            'fields': ('is_researcher', 'is_participant'),
            'description': 'These fields are read-only except for superusers.'
        }),
        ('Consent Information', {'fields': ('consent_text',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions'),
            'description': 'Staff status is required for admin access. Researcher group membership is automatically managed.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('is_researcher', 'is_participant')}),
    )

    readonly_fields = ['consent_text']

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            if 'is_researcher' not in readonly:
                readonly.append('is_researcher')
        return readonly

    def participant_id_display(self, obj):
        if obj.is_participant and not obj.is_researcher:
            return obj.participant_id
        return obj.username or obj.email
    participant_id_display.short_description = 'ID'

    def survey_progress_display(self, obj):
        """Display survey completion progress."""
        if not obj.is_participant:
            return '—'
        completed, total, percentage = obj.get_survey_progress()
        from django.utils.html import format_html
        return format_html(
            '<span style="white-space: nowrap;">{}/{} ({}%)</span>',
            completed, total, percentage
        )
    survey_progress_display.short_description = 'Survey Progress'

    def task_progress_display(self, obj):
        """Display task completion progress."""
        if not obj.is_participant:
            return '—'
        completed, total, percentage = obj.get_task_progress()
        from django.utils.html import format_html
        return format_html(
            '<span style="white-space: nowrap;">{}/{} ({}%)</span>',
            completed, total, percentage
        )
    task_progress_display.short_description = 'Task Progress'

    def overall_progress_display(self, obj):
        """Display overall completion progress with visual indicator."""
        if not obj.is_participant:
            return '—'
        percentage = obj.get_overall_progress()

        # Add visual indicator based on progress
        if percentage == 100:
            indicator = '✓'
            color = 'green'
        elif percentage > 0:
            indicator = '⧗'
            color = 'orange'
        else:
            indicator = '✗'
            color = 'red'

        from django.utils.html import format_html
        return format_html(
            '<span style="color: {}; white-space: nowrap;">{} {}%</span>',
            color, indicator, percentage
        )
    overall_progress_display.short_description = 'Overall Progress'


@admin.register(ConsentForm)
class ConsentFormAdmin(admin.ModelAdmin):
    """
    Admin configuration for ConsentForm model.
    Allows researchers and admins to edit the consent form text shown to new participants.
    """
    list_display = ['title', 'version', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content', 'version']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Consent Form Details', {
            'fields': ['title', 'version', 'is_active'],
            'description': 'Only one consent form should be active at a time. Setting this form to active will automatically deactivate others.'
        }),
        ('Consent Text', {
            'fields': ['content'],
            'description': 'This text will be displayed to participants during registration. They must agree to this text to create an account.'
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]

    def save_model(self, request, obj, form, change):
        """
        Override save to ensure only one consent form is active.
        """
        super().save_model(request, obj, form, change)
        if obj.is_active:
            self.message_user(
                request,
                f'"{obj.title}" is now the active consent form. All other consent forms have been deactivated.'
            )


@admin.register(WithdrawalText)
class WithdrawalTextAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_active', 'updated_at']
    list_filter = ['is_active']
    readonly_fields = ['updated_at']

    fieldsets = [
        ('Withdrawal Text', {
            'fields': ['is_active', 'content'],
            'description': (
                'Text shown to participants on their account page under "Withdraw from the study". '
                'Supports Markdown formatting (headings, bold, bullet lists, etc.). '
                'Only one record should be active at a time.'
            ),
        }),
        ('Metadata', {
            'fields': ['updated_at'],
            'classes': ['collapse'],
        }),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_active:
            self.message_user(
                request,
                'Withdrawal text updated and is now active.',
            )


@admin.register(WithdrawalRecord)
class WithdrawalRecordAdmin(admin.ModelAdmin):
    list_display = ['participant_id', 'exit_survey_title', 'withdrawn_at', 'response_count']
    list_filter = ['withdrawn_at', 'exit_survey_title']
    search_fields = ['participant_id']
    readonly_fields = ['participant_id', 'withdrawn_at', 'exit_survey_title', 'responses']
    actions = ['export_csv']

    def has_add_permission(self, request):
        return False

    def response_count(self, obj):
        return len(obj.responses)
    response_count.short_description = 'Responses'

    @admin.action(description='Export withdrawal records as CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="withdrawal_records_{date.today().isoformat()}.csv"'

        writer = csv.DictWriter(response, fieldnames=[
            'participant_id', 'withdrawn_at', 'exit_survey_title', 'question', 'answer',
        ])
        writer.writeheader()

        for record in queryset:
            if record.responses:
                for item in record.responses:
                    writer.writerow({
                        'participant_id': record.participant_id,
                        'withdrawn_at': record.withdrawn_at.isoformat(),
                        'exit_survey_title': record.exit_survey_title,
                        'question': item.get('question', ''),
                        'answer': item.get('answer', ''),
                    })
            else:
                # Withdrawal with no exit survey responses — still record the row
                writer.writerow({
                    'participant_id': record.participant_id,
                    'withdrawn_at': record.withdrawn_at.isoformat(),
                    'exit_survey_title': record.exit_survey_title,
                    'question': '',
                    'answer': '',
                })

        return response


