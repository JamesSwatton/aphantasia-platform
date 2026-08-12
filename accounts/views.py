from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import ResearcherInvitation, ConsentForm
from .forms import ResearcherSignupForm
from surveys.utils import get_all_results
from surveys.models import Survey, ParticipantResponse


@login_required
def account(request):
    user = request.user
    consent_form = ConsentForm.objects.filter(is_active=True).first()
    participant_id = f"PRH-{user.date_joined.year}-{user.id:04d}"
    results = get_all_results(user)

    # Feedback survey logic
    feedback_survey = None
    feedback_questions = []
    feedback_submitted = request.GET.get('feedback') == 'submitted'
    feedback_already_done = False

    active_feedback = Survey.objects.filter(is_feedback=True, is_active=True).first()
    if active_feedback:
        completed_count = ParticipantResponse.objects.filter(
            participant=user,
            survey__is_feedback=False,
            is_test=False,
        ).values('survey').distinct().count()

        already_responded = ParticipantResponse.objects.filter(
            participant=user,
            survey=active_feedback,
            is_test=False,
        ).exists()

        if already_responded:
            feedback_already_done = True
        elif completed_count >= active_feedback.show_after_n_surveys:
            feedback_survey = active_feedback
            feedback_questions = list(active_feedback.questions.order_by('order'))

    return render(request, 'accounts/account.html', {
        'participant_id': participant_id,
        'consent_form': consent_form,
        'results': results,
        'feedback_survey': feedback_survey,
        'feedback_questions': feedback_questions,
        'feedback_submitted': feedback_submitted,
        'feedback_already_done': feedback_already_done,
    })


@login_required
def feedback_submit(request):
    if request.method != 'POST':
        return redirect('accounts:account')

    survey_id = request.POST.get('survey_id')
    survey = get_object_or_404(Survey, id=survey_id, is_feedback=True, is_active=True)
    user = request.user

    # Prevent double submission
    if ParticipantResponse.objects.filter(participant=user, survey=survey, is_test=False).exists():
        return redirect('accounts:account')

    skipped = request.POST.get('skip') == '1'
    questions = survey.questions.order_by('order')
    for question in questions:
        if skipped:
            answer = 'NULL'
        else:
            raw = request.POST.get(f'question_{question.id}', '').strip()

            if question.question_type == 'likert':
                if raw:
                    try:
                        answer = int(raw)
                        if question.reverse_coded:
                            answer = question.apply_reverse_coding(answer)
                        answer = str(question.apply_scale_factor(answer))
                    except ValueError:
                        answer = 'NULL'
                else:
                    answer = 'NULL'
            else:
                answer = raw if raw else 'NULL'

        ParticipantResponse.objects.create(
            survey=survey,
            question=question,
            participant=user,
            answer=answer,
            is_test=False,
        )

    return redirect(reverse('accounts:account') + '?feedback=submitted')


def accept_invitation(request, token):
    """
    View for accepting a researcher invitation and registering.
    """
    # Get the invitation by token
    invitation = get_object_or_404(ResearcherInvitation, token=token)

    # Check if the invitation is valid
    if invitation.used:
        messages.error(request, 'This invitation has already been used.')
        return redirect('account_login')

    if invitation.is_expired():
        messages.error(request, 'This invitation has expired. Please contact the person who invited you to request a new invitation.')
        return redirect('account_login')

    # Handle form submission
    if request.method == 'POST':
        form = ResearcherSignupForm(request.POST, invitation=invitation)
        if form.is_valid():
            # Create the user
            user = form.save()

            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Show success message
            messages.success(
                request,
                f'Welcome! Your researcher account has been created successfully. You now have access to the admin panel.'
            )

            # Redirect to admin panel
            return redirect('admin:index')
    else:
        form = ResearcherSignupForm(invitation=invitation)

    context = {
        'form': form,
        'invitation': invitation,
    }

    return render(request, 'accounts/accept_invitation.html', context)
