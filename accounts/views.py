from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import markdown as md
from .models import ConsentForm, WithdrawalText, WithdrawalRecord
from surveys.utils import get_all_results
from surveys.models import Survey, ParticipantResponse


@login_required
def account(request):
    user = request.user
    consent_form = ConsentForm.objects.filter(is_active=True).first()
    consent_form_html = md.markdown(
        consent_form.content,
        extensions=['sane_lists', 'nl2br'],
    ) if consent_form else None

    withdrawal_text_obj = WithdrawalText.objects.filter(is_active=True).first()
    withdrawal_text_html = md.markdown(
        withdrawal_text_obj.content,
        extensions=['sane_lists', 'nl2br'],
    ) if withdrawal_text_obj else None
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
        'consent_form_html': consent_form_html,
        'results': results,
        'feedback_survey': feedback_survey,
        'feedback_questions': feedback_questions,
        'feedback_submitted': feedback_submitted,
        'feedback_already_done': feedback_already_done,
        'withdrawal_text_html': withdrawal_text_html,
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


@login_required
def exit_survey(request):
    from surveys.models import ExitSurvey
    active_exit = ExitSurvey.objects.filter(is_active=True, is_exit_survey=True).first()
    exit_questions = list(active_exit.questions.order_by('order')) if active_exit else []

    return render(request, 'accounts/exit_survey.html', {
        'exit_survey': active_exit,
        'exit_questions': exit_questions,
    })


@login_required
def exit_survey_submit(request):
    if request.method != 'POST':
        return redirect('accounts:exit_survey')

    from surveys.models import ExitSurvey
    from django.contrib.auth import logout

    user = request.user
    action = request.POST.get('action', 'skip')
    survey_id = request.POST.get('survey_id')

    if survey_id:
        try:
            survey = ExitSurvey.objects.get(id=survey_id, is_active=True, is_exit_survey=True)
            if action == 'submit':
                for question in survey.questions.order_by('order'):
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
        except ExitSurvey.DoesNotExist:
            pass

    # Build anonymised participant ID before deleting the user
    participant_id = f"PRH-{user.date_joined.year}-{user.id:04d}"

    # Snapshot exit survey responses if any were just saved
    exit_survey_title = ''
    response_snapshot = []
    if survey_id and action == 'submit':
        try:
            from surveys.models import ExitSurvey
            survey_obj = ExitSurvey.objects.get(id=survey_id)
            exit_survey_title = survey_obj.title
            for r in ParticipantResponse.objects.filter(
                participant=user, survey=survey_obj
            ).select_related('question').order_by('question__order'):
                response_snapshot.append({
                    'question': r.question.text,
                    'answer': r.answer,
                })
        except Exception:
            pass

    WithdrawalRecord.objects.create(
        participant_id=participant_id,
        exit_survey_title=exit_survey_title,
        responses=response_snapshot,
    )

    # Send withdrawal confirmation before deleting — email address unavailable after
    try:
        context = {'email': user.email, 'participant_id': participant_id}
        subject = render_to_string('account/email/withdrawal_confirmation_subject.txt', context).strip()
        message = render_to_string('account/email/withdrawal_confirmation_message.txt', context)
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@phantasiaresearchhub.com'),
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:
        pass

    logout(request)
    user.delete()
    return redirect('accounts:withdrawal_complete')


def withdrawal_complete(request):
    return render(request, 'accounts/withdrawal_complete.html')


