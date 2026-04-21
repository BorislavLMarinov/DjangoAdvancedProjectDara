from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='rarity_badge')
def rarity_badge(value):
    """
    Custom filter to style rarity labels with stars and K-POP neon themes.
    Usage: {{ avatar.rarity|rarity_badge }}
    """
    rarities = {
        'common': ('★', '#6c757d'),
        'rare': ('★★', '#0dcaf0'),
        'epic': ('★★★', '#6610f2'),
        'legendary': ('★★★★', '#fd7e14'),
        'limited': ('★★★★★', '#d63384'),
        'achievement': ('🏆', '#ffc107'),
    }
    
    val = value.lower() if value else 'common'
    icon, color = rarities.get(val, ('★', '#6c757d'))
    
    html = f'<span class="badge" style="background-color: {color};">{icon} {value.upper()}</span>'
    return mark_safe(html)

@register.filter(name='xp_to_percent')
def xp_to_percent(current, next_level):
    """Calculates percentage for progress bars."""
    if not next_level or next_level == 0:
        return 0
    return round((current / next_level) * 100, 1)
