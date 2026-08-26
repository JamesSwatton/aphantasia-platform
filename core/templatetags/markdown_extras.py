import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

MARKDOWN_EXTENSIONS = ['sane_lists', 'nl2br']


def markdown_to_html(value):
    """
    The single source of truth for Markdown rendering across the site
    (survey/exit-survey copy, consent form, withdrawal text, messages).
    Returns a plain (non-safe) HTML string; callers needing a safe string
    for direct template interpolation should use the render_markdown
    filter below instead.
    """
    return markdown.markdown(value or '', extensions=MARKDOWN_EXTENSIONS)


@register.filter
def render_markdown(value):
    return mark_safe(markdown_to_html(value))
