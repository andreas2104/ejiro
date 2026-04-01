"""
app/widgets/list_items.py — General-purpose list-item widgets for Clients,
Lamps, Loans and Transactions screens.
"""
from kivy.properties import StringProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout


class ClientListItem(ButtonBehavior, BoxLayout):
    """Tappable row showing client name, phone and address."""
    client_name = StringProperty()
    client_telephone = StringProperty()
    client_adresse = StringProperty()
    client_id = None


class LampListItem(ButtonBehavior, BoxLayout):
    """Tappable row showing lamp number and status."""
    lamp_numero = StringProperty()
    lamp_etat = StringProperty()
    lamp_id = None


class LoanListItem(BoxLayout):
    """Non-tappable row showing loan summary (used in read-only lists)."""
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    loan_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class LoanListItemWithSelect(ButtonBehavior, BoxLayout):
    """Tappable loan row used in LoanScreen for selection."""
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    loan_id = None


class TransactionListItem(ButtonBehavior, BoxLayout):
    """Tappable row in the History screen, colour-coded by day of week."""
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    date_paiement = StringProperty()
    montant = StringProperty()
    day_color = ListProperty([0.5, 0.5, 0.5, 1])
    transaction_id = None
