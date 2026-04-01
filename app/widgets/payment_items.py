"""
app/widgets/payment_items.py — Payment-related widget rows.
"""
import logging

from kivy.app import App
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout

logger = logging.getLogger(__name__)


class ClientPaymentItem(ButtonBehavior, BoxLayout):
    """Row in PaymentScreen showing a client/lamp pair with paid toggle."""
    client_nom = StringProperty()
    client_telephone = StringProperty()
    client_adresse = StringProperty()
    total_journalier = StringProperty()
    lamps_info = StringProperty()
    is_paid = BooleanProperty(False)
    client_id = None
    pret_id = None
    client_data = None

    def on_paid_toggle(self, is_paid):
        app = App.get_running_app()
        payment_screen = app.root.ids.screen_manager.get_screen("payment")
        payment_screen.on_client_paid_toggle(self, is_paid)


class DailyPaymentListItem(BoxLayout):
    """Row used in daily-payment list with checkbox state."""
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    is_paid = BooleanProperty(False)
    loan_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_checkbox_active")

    def on_checkbox_active(self, *args):
        pass
