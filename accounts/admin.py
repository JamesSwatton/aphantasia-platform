from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from allauth.account.models import EmailAddress
from .models import User, ConsentForm, ResearcherInvitation
from .forms import InviteResearcherForm

# Unregister allauth's EmailAddress model from admin
# We don't need manual management of email verification records
admin.site.unregister(EmailAddress)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    Note: Researchers should be appointed via invitation system, not manual promotion.
    """
    list_display = ['username', 'email', 'is_researcher', 'is_participant', 'survey_progress_display', 'task_progress_display', 'overall_progress_display', 'is_active', 'date_joined']
    list_filter = ['is_researcher', 'is_participant', 'is_active', 'date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role Information', {
            'fields': ('is_researcher', 'is_participant'),
            'description': 'Researchers are appointed via invitation system. These fields are read-only except for superusers.'
        }),
        ('Consent Information', {'fields': ('consent_text',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_superuser', 'user_permissions'),
            'description': 'Note: Researcher group membership and staff status are automatically managed.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('is_participant',)}),
    )

    readonly_fields = ['consent_text', 'is_researcher']

    def get_readonly_fields(self, request, obj=None):
        """
        Make is_researcher read-only for non-superusers.
        Superusers can still manually adjust in emergency situations.
        """
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            if 'is_researcher' not in readonly:
                readonly.append('is_researcher')
        return readonly

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


@admin.register(ResearcherInvitation)
class ResearcherInvitationAdmin(admin.ModelAdmin):
    """
    Admin configuration for ResearcherInvitation model.
    Allows researchers to invite new researchers to join the platform.
    """
    list_display = ['email', 'invited_by', 'created_at', 'expires_at', 'used', 'get_status']
    list_filter = ['used', 'created_at', 'expires_at']
    search_fields = ['email', 'invited_by__email']
    readonly_fields = ['token', 'created_at', 'used_at', 'invited_by']
    actions = ['resend_invitation']

    fieldsets = [
        ('Invitation Details', {
            'fields': ['email', 'invited_by', 'token'],
        }),
        ('Status', {
            'fields': ['used', 'used_at', 'expires_at'],
        }),
        ('Metadata', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]

    def get_status(self, obj):
        """
        Display the current status of the invitation.
        """
        if obj.used:
            return "✓ Used"
        elif obj.is_expired():
            return "✗ Expired"
        else:
            return "⧗ Pending"
    get_status.short_description = "Status"

    def has_add_permission(self, request):
        """
        Disable the default add form - users should use the custom invite form.
        """
        return False

    def get_urls(self):
        """
        Add custom URL for sending invitations.
        """
        urls = super().get_urls()
        custom_urls = [
            path('invite/', self.admin_site.admin_view(self.invite_researcher_view), name='accounts_researcherinvitation_invite'),
        ]
        return custom_urls + urls

    def invite_researcher_view(self, request):
        """
        Custom view for inviting a new researcher.
        """
        if request.method == 'POST':
            form = InviteResearcherForm(request.POST, invited_by=request.user)
            if form.is_valid():
                try:
                    invitation = form.save(request)
                    messages.success(
                        request,
                        f'Invitation sent successfully to {invitation.email}. The invitation will expire on {invitation.expires_at.strftime("%Y-%m-%d %H:%M")}.'
                    )
                    return redirect('admin:accounts_researcherinvitation_changelist')
                except Exception as e:
                    messages.error(request, f'Failed to send invitation: {str(e)}')
        else:
            form = InviteResearcherForm(invited_by=request.user)

        context = {
            'form': form,
            'title': 'Invite New Researcher',
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/accounts/invite_researcher.html', context)

    @admin.action(description='Resend invitation email')
    def resend_invitation(self, request, queryset):
        """
        Resend invitation emails for selected invitations.
        Only works for pending (not used, not expired) invitations.
        """
        from django.core.mail import send_mail
        from django.urls import reverse
        from django.conf import settings

        resent_count = 0
        for invitation in queryset:
            if invitation.is_valid():
                # Build the invitation URL
                invitation_url = request.build_absolute_uri(
                    reverse('accounts:accept_invitation', kwargs={'token': str(invitation.token)})
                )

                # Resend the email
                try:
                    send_mail(
                        subject='Reminder: Invitation to Join as a Researcher - Aphantasia Research Platform',
                        message=f"""Hello,

This is a reminder that you have been invited by {invitation.invited_by.email} to join the Aphantasia Research Platform as a researcher.

To accept this invitation and create your researcher account, please click the link below:

{invitation_url}

This invitation will expire on {invitation.expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}.

If you did not expect this invitation, you can safely ignore this email.

Best regards,
Aphantasia Research Platform Team
""",
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@example.com',
                        recipient_list=[invitation.email],
                        fail_silently=False,
                    )
                    resent_count += 1
                except Exception as e:
                    messages.error(request, f'Failed to resend invitation to {invitation.email}: {str(e)}')

        if resent_count > 0:
            self.message_user(
                request,
                f'{resent_count} invitation(s) resent successfully.',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                'No valid invitations to resend. Invitations must be pending (not used and not expired).',
                messages.WARNING
            )
