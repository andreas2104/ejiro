"""
app/widgets/stat_card.py — Dashboard StatCard widget.
"""
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.card import MDCard


class StatCard(MDCard, ButtonBehavior):
    """Tappable card displayed on the dashboard with icon, title and value."""
    title = StringProperty()
    value = StringProperty()
    icon = StringProperty()
