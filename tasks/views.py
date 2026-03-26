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

    # Start with all tasks
    tasks = LabTask.objects.all()

    # Apply domain filter if provided
    domain_id = request.GET.get('domain')
    if domain_id:
        if domain_id == 'none':
            # Filter for tasks with no domain
            tasks = tasks.filter(domain__isnull=True)
        else:
            # Filter for specific domain
            tasks = tasks.filter(domain_id=domain_id)

    # Get all domains for the filter dropdown
    from core.models import Domain
    domains = Domain.objects.all()

    context = {
        'tasks': tasks,
        'domains': domains,
        'selected_domain': domain_id,
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

    # Notify researchers they are in test mode — data will be saved but flagged
    if request.user.is_researcher or request.user.is_staff:
        messages.info(
            request,
            "You are running this task in test mode. "
            "Your submission will be saved and flagged as a test so it can be reviewed and deleted."
        )

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

    # If restarting a completed task, reset status and start time
    if submission.status == 'completed':
        TaskSubmission.objects.filter(pk=submission.pk).update(
            status='in_progress',
            started_at=timezone.now(),
            completed_at=None,
            time_spent_seconds=None,
        )
        submission.refresh_from_db()

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

        # Only set completed_at and recalculate time if task_submit hasn't already done so.
        # task_submit sets completed_at and time_spent_seconds with accurate in-task timing.
        # The confirm button here is a UI step only — we don't want to overwrite the real timing.
        if not submission.completed_at:
            submission.completed_at = timezone.now()
        if not submission.time_spent_seconds and submission.started_at:
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

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)

        # Flag submissions from researchers/staff as test data
        is_test = request.user.is_researcher or request.user.is_staff

        # Get or create submission
        submission, created = TaskSubmission.objects.get_or_create(
            task=task,
            participant=request.user,
            defaults={'status': 'started', 'is_test': is_test}
        )

        # Update submission with results
        submission.results_data = data
        submission.status = 'completed'
        submission.completed_at = timezone.now()
        submission.is_test = is_test

        # Extract task duration directly from lab.js data.
        # The 'Task' sender row contains a 'duration' field in milliseconds,
        # recorded by lab.js itself. This reflects only time spent inside the
        # task, which is more meaningful for research than server-side diffs
        # (which include instructions page, network latency, complete page, etc.)
        task_row = next((r for r in data if r.get('sender') == 'Task'), None)
        if task_row and task_row.get('duration'):
            submission.time_spent_seconds = int(task_row['duration'] / 1000)
        elif submission.started_at:
            # Fallback to server-side diff if no Task row present in data
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
