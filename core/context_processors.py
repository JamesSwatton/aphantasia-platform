from .views import _visible_messages


def unread_message_count(request):
    if not request.user.is_authenticated:
        return {'unread_message_count': 0}
    read_ids = set(request.user.read_messages.values_list('id', flat=True))
    count = sum(1 for msg in _visible_messages(request.user) if msg.id not in read_ids)
    return {'unread_message_count': count}
