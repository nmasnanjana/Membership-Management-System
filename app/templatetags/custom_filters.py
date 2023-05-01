from django import template

register = template.Library()

@register.filter(name='addleadingzeros')
def add_leading_zeros(value, num_zeros=4):
    return str(value).zfill(num_zeros)