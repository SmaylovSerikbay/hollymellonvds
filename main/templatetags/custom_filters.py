from django import template

register = template.Library()

@register.filter
def split(value, delimiter='\n\n'):
    """
    Разделяет строку по указанному разделителю.
    По умолчанию разделяет по двойному переносу строки.
    """
    if not value:
        return []
    return value.split(delimiter) 