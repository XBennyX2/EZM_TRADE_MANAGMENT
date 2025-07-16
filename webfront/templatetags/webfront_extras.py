from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def currency(value):
    """Format value as currency."""
    try:
        return f"ETB {Decimal(str(value)):,.2f}"
    except (ValueError, TypeError):
        return "ETB 0.00"

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total."""
    try:
        if total == 0:
            return 0
        return (Decimal(str(value)) / Decimal(str(total))) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
