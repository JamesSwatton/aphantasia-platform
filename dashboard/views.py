from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from surveys.models import Survey, ParticipantResponse
from tasks.models import LabTask, TaskSubmission


@login_required
def participant_dashboard(request):
    """
    Dashboard view for participants showing available surveys, tasks, and their progress.
    Researchers are redirected to the survey management page.
    """
    # Redirect researchers to their survey management interface
    if request.user.is_researcher or request.user.is_staff:
        messages.info(
            request,
            "As a researcher, please use the Survey Management page to preview and test surveys."
        )
        return redirect('surveys:survey_list')

    # Get all active surveys (ordered by priority, then by created_at via model Meta)
    active_surveys = Survey.objects.filter(is_active=True)

    # Get surveys the participant has completed (has any response)
    completed_survey_ids = ParticipantResponse.objects.filter(
        participant=request.user
    ).values_list('survey_id', flat=True).distinct()

    # Split surveys into completed and available
    completed_surveys = []
    available_surveys = []

    for survey in active_surveys:
        # Count how many questions they've answered
        response_count = ParticipantResponse.objects.filter(
            survey=survey,
            participant=request.user
        ).count()

        # Count total questions in survey
        total_questions = survey.questions.count()

        survey_data = {
            'survey': survey,
            'response_count': response_count,
            'total_questions': total_questions,
            'is_complete': response_count > 0,  # Has at least one response
        }

        if survey.id in completed_survey_ids:
            completed_surveys.append(survey_data)
        else:
            available_surveys.append(survey_data)

    # Get all active tasks (ordered by priority, then by created_at via model Meta)
    active_tasks = LabTask.objects.filter(is_active=True, task_directory__isnull=False)

    # Get tasks the participant has completed
    completed_task_ids = TaskSubmission.objects.filter(
        participant=request.user,
        status='completed'
    ).values_list('task_id', flat=True).distinct()

    # Split tasks into completed and available
    completed_tasks = []
    available_tasks = []

    for task in active_tasks:
        # Get submission if it exists
        try:
            submission = TaskSubmission.objects.get(task=task, participant=request.user)
            task_data = {
                'task': task,
                'submission': submission,
                'is_complete': submission.status == 'completed',
            }
        except TaskSubmission.DoesNotExist:
            task_data = {
                'task': task,
                'submission': None,
                'is_complete': False,
            }

        if task.id in completed_task_ids:
            completed_tasks.append(task_data)
        else:
            available_tasks.append(task_data)

    context = {
        'available_surveys': available_surveys,
        'completed_surveys': completed_surveys,
        'available_tasks': available_tasks,
        'completed_tasks': completed_tasks,
    }

    return render(request, 'dashboard/participant_dashboard.html', context)
