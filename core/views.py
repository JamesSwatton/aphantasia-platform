from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Message


def home(request):
    return render(request, 'home.html')


@login_required
def messages_view(request):
    published = Message.objects.filter(is_published=True)
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
    try:
        message = Message.objects.get(id=message_id, is_published=True)
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    message.read_by.add(request.user)
    unread_count = Message.objects.filter(is_published=True).exclude(read_by=request.user).count()
    return JsonResponse({'unread_count': unread_count})


@login_required
@require_POST
def mark_all_read(request):
    published = Message.objects.filter(is_published=True)
    for message in published:
        message.read_by.add(request.user)
    return JsonResponse({'unread_count': 0})
