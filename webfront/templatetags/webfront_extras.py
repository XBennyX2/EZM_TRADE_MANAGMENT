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


@register.filter
def add_tax(value, include_tax=True):
    """Add 15% tax to value if include_tax is True."""
    try:
        subtotal = Decimal(str(value))
        if include_tax:
            tax_amount = subtotal * Decimal('0.15')
            return subtotal + tax_amount
        return subtotal
    except (ValueError, TypeError):
        return value


@register.filter
def calculate_tax(value):
    """Calculate 15% tax amount."""
    try:
        return Decimal(str(value)) * Decimal('0.15')
    except (ValueError, TypeError):
        return 0


@register.filter
def format_tax_breakdown(value, include_tax=True):
    """Format tax breakdown for display."""
    try:
        subtotal = Decimal(str(value))
        if include_tax:
            tax_amount = subtotal * Decimal('0.15')
            total = subtotal + tax_amount
            return {
                'subtotal': subtotal,
                'tax': tax_amount,
                'total': total,
                'include_tax': True
            }
        return {
            'subtotal': subtotal,
            'tax': Decimal('0'),
            'total': subtotal,
            'include_tax': False
        }
    except (ValueError, TypeError):
        return {
            'subtotal': Decimal('0'),
            'tax': Decimal('0'),
            'total': Decimal('0'),
            'include_tax': include_tax
        }
