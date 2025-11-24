from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from .models import LabTask, TaskSubmission
import json


@login_required
def task_list(request):
    """
    List all lab.js tasks for researchers only.
    Participants should use the participant dashboard instead.
    """
    # Check if user is researcher or staff
    if not (request.user.is_researcher or request.user.is_staff):
        messages.error(request, "Only researchers can access the task management page.")
        return redirect('dashboard:participant_dashboard')

    # Researchers can see all tasks
    tasks = LabTask.objects.all()

    context = {
        'tasks': tasks,
        'is_researcher': True,
    }

    return render(request, 'tasks/task_list.html', context)


@login_required
def task_preview(request, pk):
    """
    Preview view for researchers to see how the task will be rendered.
    Opens the lab.js task directly in the browser.
    """
    task = get_object_or_404(LabTask, pk=pk)

    # Check if user is researcher or staff
    if not (request.user.is_researcher or request.user.is_staff):
        return HttpResponseForbidden("Only researchers can preview tasks.")

    # Check if task has been unpacked
    if not task.task_directory:
        messages.error(request, "This task has not been properly unpacked yet.")
        return redirect('tasks:task_list')

    # Show instructions page first if not already seen
    if task.instructions and not request.GET.get('start'):
        context = {
            'task': task,
            'show_instructions': True,
            'is_preview': True,
        }
        return render(request, 'tasks/task_start.html', context)

    # Redirect to the actual lab.js task
    task_url = task.get_index_url()
    return redirect(task_url)


@login_required
def task_run(request, pk):
    """
    View for participants to run a lab.js task.
    Researchers are redirected to preview mode to prevent data contamination.

    This view serves the lab.js HTML directly to avoid CORS issues with iframes.
    """
    task = get_object_or_404(LabTask, pk=pk)

    # Redirect researchers to preview mode to prevent data contamination
    if request.user.is_researcher or request.user.is_staff:
        messages.info(
            request,
            "As a researcher, you've been redirected to preview mode. "
            "Your task results will not be saved to the database."
        )
        return redirect('tasks:task_preview', pk=pk)

    # Check if task is active
    if not task.is_active:
        messages.error(request, "This task is not currently active.")
        return redirect('dashboard:participant_dashboard')

    # Check if task has been unpacked
    if not task.task_directory:
        messages.error(request, "This task is not available yet.")
        return redirect('dashboard:participant_dashboard')

    # Get or create task submission
    submission, created = TaskSubmission.objects.get_or_create(
        task=task,
        participant=request.user,
        defaults={'status': 'started'}
    )

    # If restarting a completed task, reset status
    if submission.status == 'completed':
        submission.status = 'in_progress'
        submission.save()

    # Show instructions page first if task has instructions
    if task.instructions and not request.GET.get('start'):
        context = {
            'task': task,
            'submission': submission,
            'show_instructions': True,
        }
        return render(request, 'tasks/task_start.html', context)

    # Redirect to the actual lab.js task (served as media)
    # The task will open in the same window, avoiding iframe issues
    task_url = task.get_index_url()
    return redirect(task_url)


@login_required
def task_complete(request, pk):
    """
    Completion page where participants confirm they've finished the task.
    This is where lab.js tasks redirect after completion.
    """
    task = get_object_or_404(LabTask, pk=pk)

    # Get or create the submission
    submission, created = TaskSubmission.objects.get_or_create(
        task=task,
        participant=request.user,
        defaults={'status': 'started'}
    )

    # Handle the completion form submission
    if request.method == 'POST':
        submission.status = 'completed'
        submission.completed_at = timezone.now()

        # Calculate time spent
        if submission.started_at:
            time_diff = submission.completed_at - submission.started_at
            submission.time_spent_seconds = int(time_diff.total_seconds())

        submission.save()

        messages.success(
            request,
            f"Thank you! Your completion of '{task.title}' has been recorded."
        )
        return redirect('dashboard:participant_dashboard')

    # Show the completion page
    context = {
        'task': task,
        'submission': submission,
    }

    return render(request, 'tasks/task_complete.html', context)


@csrf_exempt
@login_required
def task_submit(request, pk):
    """
    API endpoint for submitting lab.js task results.
    Accepts POST requests with JSON data from lab.js.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    task = get_object_or_404(LabTask, pk=pk)

    # Don't save data from researchers
    if request.user.is_researcher or request.user.is_staff:
        return JsonResponse({
            'status': 'preview',
            'message': 'Preview mode: Data not saved'
        })

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)

        # Get or create submission
        submission, created = TaskSubmission.objects.get_or_create(
            task=task,
            participant=request.user,
            defaults={'status': 'started'}
        )

        # Update submission with results
        submission.results_data = data
        submission.status = 'completed'
        submission.completed_at = timezone.now()

        # Calculate time spent if start time is available
        if submission.started_at:
            time_diff = submission.completed_at - submission.started_at
            submission.time_spent_seconds = int(time_diff.total_seconds())

        submission.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Results saved successfully',
            'submission_id': submission.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
