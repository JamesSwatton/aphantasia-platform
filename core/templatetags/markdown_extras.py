import re

import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

MARKDOWN_EXTENSIONS = ['sane_lists', 'nl2br']
FOOTNOTE_RE = re.compile(r'<p>(\* .*?)</p>\s*', re.DOTALL)


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


@register.filter
def question_body(value):
    """Question text as HTML, without its footnotes (see question_notes)."""
    return mark_safe(FOOTNOTE_RE.sub('', markdown_to_html(value)).strip())


@register.filter
def question_notes(value):
    """
    Footnote paragraphs of a question, typed as a line starting "\\* ".
    Kept apart from question_body because the question's styling relies on
    its last block being the question itself.
    """
    return mark_safe(''.join(
        '<p class="q-note">{}</p>'.format(note)
        for note in FOOTNOTE_RE.findall(markdown_to_html(value))
    ))
