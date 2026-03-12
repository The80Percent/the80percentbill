import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import SafeData, mark_safe

register = template.Library()


@register.filter(name="footnotes", is_safe=True, needs_autoescape=True)
def footnotes(text, autoescape=True):
    """Convert [1], [2], etc. in narrative text to superscript anchor links."""
    # If input is already marked safe (e.g. from |linebreaks), preserve it.
    # Otherwise, escape to prevent XSS.
    if autoescape and not isinstance(text, SafeData):
        text = conditional_escape(text)

    def replace_ref(match):
        num = match.group(1)
        return f'<sup><a href="#source-{num}" class="footnote-ref">[{num}]</a></sup>'

    result = re.sub(r"\[(\d+)\]", replace_ref, str(text))
    return mark_safe(result)
