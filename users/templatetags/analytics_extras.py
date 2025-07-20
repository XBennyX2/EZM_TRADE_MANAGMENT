from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Template filter to lookup a value in a dictionary by key.
    Usage: {{ dictionary|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []

@register.filter
def multiply(value, arg):
    """
    Template filter to multiply two values.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Template filter to calculate percentage.
    Usage: {{ value|percentage:total }}
    """
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """
    Template filter to format currency.
    Usage: {{ value|currency }}
    """
    try:
        return "ETB {:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "ETB 0.00"

@register.filter
def stock_status_text(value):
    """Convert stock out frequency to status text."""
    try:
        freq = int(value or 0)
        if freq == 0:
            return "Perfect"
        elif freq <= 2:
            return "Good"
        elif freq <= 5:
            return "Monitor"
        else:
            return "Critical"
    except (ValueError, TypeError):
        return "Unknown"

@register.filter
def stock_status_class(value):
    """Convert stock out frequency to CSS class."""
    try:
        freq = int(value or 0)
        if freq == 0:
            return "status-excellent"
        elif freq <= 2:
            return "status-good"
        elif freq <= 5:
            return "status-warning"
        else:
            return "status-critical"
    except (ValueError, TypeError):
        return "status-critical"
