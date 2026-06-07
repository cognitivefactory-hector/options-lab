"""Small presentation-only template filters for the Options Lab UI."""
from django import template

register = template.Library()


@register.filter
def pct(value, digits=1):
    """Render a 0..1 fraction as a percentage, e.g. 0.426 -> "42.6%"."""
    try:
        return f"{float(value) * 100:.{int(digits)}f}%"
    except (TypeError, ValueError):
        return value


@register.filter
def money(value):
    """Render a number as a $ amount with thousands separators."""
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return value
