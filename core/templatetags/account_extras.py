from django import template

register = template.Library()


@register.filter
def initials(value):
    """Return up to two initials: first letter of first and last word."""
    words = (value or '').strip().split()
    if not words:
        return ''
    if len(words) == 1:
        return words[0][0].upper()
    return (words[0][0] + words[-1][0]).upper()
