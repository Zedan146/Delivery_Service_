from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_timedelta(value):
    """Форматирует timedelta в формат ЧЧ:ММ:СС без миллисекунд"""
    if not isinstance(value, timedelta):
        return value
    
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}" 