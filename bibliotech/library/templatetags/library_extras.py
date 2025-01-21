from django import template
from library.models import Category

register = template.Library()

@register.filter
def get_category_name(categories, category_id):
    try:
        return categories.get(id=category_id).name
    except Category.DoesNotExist:
        return "Catégorie inconnue"

@register.filter
def get_range(value):
    return range(value)