from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)

@register.filter
def get_block_display(block_code):
    BLOCK_CHOICES = [
        ('bloque_15', 'BLOQUE 15'),
        ('bloque_16', 'BLOQUE 16'),
        ('bloque_17', 'BLOQUE 17'),
        ('bloque_22p', 'BLOQUE 22 P'),
        ('bloque_23p', 'BLOQUE 23 P'),
        ('bloque_24p', 'BLOQUE 24 P'),
        ('bloque_25p', 'BLOQUE 25 P'),
        ('bloque_18', 'BLOQUE 18'),
        ('bloque_19', 'BLOQUE 19'),
        ('bloque_20', 'BLOQUE 20'),
        ('bloque_21', 'BLOQUE 21'),
        ('otro', 'OTRO'),
    ]
    
    for code, display in BLOCK_CHOICES:
        if code == block_code:
            return display
    return block_code

@register.filter
def get_resolution_display(method_code):
    RESOLUTION_METHOD_CHOICES = [
        ('conciliacion', 'Conciliación'),
        ('mediacion', 'Mediación'),
        ('equidad', 'Resolución en equidad'),
        ('otro', 'Otro'),
    ]
    
    for code, display in RESOLUTION_METHOD_CHOICES:
        if code == method_code:
            return display
    return method_code