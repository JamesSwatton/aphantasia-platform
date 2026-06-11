from .models import Message


def unread_message_count(request):
    if not request.user.is_authenticated:
        return {'unread_message_count': 0}
    count = Message.objects.filter(is_published=True).exclude(read_by=request.user).count()
    return {'unread_message_count': count}
