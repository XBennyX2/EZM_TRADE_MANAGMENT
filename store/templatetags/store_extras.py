from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(date, days):
    """Add days to a date"""
    if date:
        return date + timedelta(days=days)
    return None

@register.filter
def display_role(role):
    """Display user-friendly role names"""
    role_mapping = {
        'cashier': 'Salesperson',
        'store_manager': 'Store Manager',
        'head_manager': 'Head Manager',
        'admin': 'Administrator',
    }
    return role_mapping.get(role, role.title() if role else 'User')
