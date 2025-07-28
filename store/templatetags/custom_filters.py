# store/templatetags/custom_filters.py

from django import template
# CHANGE THIS LINE:
# from django.forms.bound import BoundField
# TO THIS:
from django.forms import BoundField # BoundField is directly available under django.forms

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a Django form field's widget.
    Usage: {{ form.my_field|add_class:"my-custom-class" }}
    """
    # Ensure 'field' is a BoundField and has a widget
    if not isinstance(field, BoundField) or not hasattr(field.field, 'widget'):
        # If it's not a proper form field, return it unchanged.
        # This prevents the AttributeError if something else (like a string)
        # is accidentally piped through this filter.
        return field

    # Access the widget associated with the BoundField
    widget = field.field.widget

    # Get a mutable copy of the widget's current attributes
    attrs = widget.attrs.copy()

    # Append the new CSS class
    if 'class' in attrs:
        # If 'class' attribute already exists, append the new class with a space
        attrs['class'] += ' ' + css_class
    else:
        # If 'class' attribute does not exist, set it
        attrs['class'] = css_class

    # Render the BoundField with the modified attributes
    # The 'renderer' argument ensures compatibility with Django's form rendering
    return field.as_widget(attrs=attrs, renderer=field.form.renderer)