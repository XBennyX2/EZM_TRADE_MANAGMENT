from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(date, days):
    """Add days to a date"""
    if date:
        return date + timedelta(days=days)
    return None
