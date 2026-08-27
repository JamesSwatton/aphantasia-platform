from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Message
from surveys.utils import get_completed_survey_count

MAX_VISIBLE_MESSAGES = 8


def home(request):
    return render(request, 'home.html')


def _visible_messages(user):
    """
    Published messages the given user is currently allowed to see: an
    unlocks_with_survey message is held back until the user has completed
    at least that survey's show_after_n_surveys count. Capped to the
    MAX_VISIBLE_MESSAGES most recent, so the list doesn't grow unbounded.
    """
    published = Message.objects.filter(is_published=True).select_related('unlocks_with_survey')
    completed_count = None

    visible = []
    for msg in published:
        if msg.unlocks_with_survey_id is not None:
            if completed_count is None:
                completed_count = get_completed_survey_count(user)
            if completed_count < msg.unlocks_with_survey.show_after_n_surveys:
                continue
        visible.append(msg)
        if len(visible) == MAX_VISIBLE_MESSAGES:
            break
    return visible


@login_required
def messages_view(request):
    published = _visible_messages(request.user)
    read_ids = set(request.user.read_messages.values_list('id', flat=True))

    annotated = []
    for msg in published:
        annotated.append({
            'message': msg,
            'is_unread': msg.id not in read_ids,
        })

    total = len(annotated)
    unread_count = sum(1 for m in annotated if m['is_unread'])

    return render(request, 'core/messages.html', {
        'annotated_messages': annotated,
        'total': total,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_read(request, message_id):
    visible = _visible_messages(request.user)
    visible_ids = {msg.id for msg in visible}
    if message_id not in visible_ids:
        return JsonResponse({'error': 'Not found'}, status=404)
    message = Message.objects.get(id=message_id)
    message.read_by.add(request.user)
    read_ids = set(request.user.read_messages.values_list('id', flat=True))
    unread_count = sum(1 for msg in visible if msg.id not in read_ids)
    return JsonResponse({'unread_count': unread_count})


@login_required
@require_POST
def mark_all_read(request):
    for message in _visible_messages(request.user):
        message.read_by.add(request.user)
    return JsonResponse({'unread_count': 0})
