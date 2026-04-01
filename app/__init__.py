"""
app/__init__.py — EJiroApp: the KivyMD application class.

All widget and screen classes are imported here before the KV file is loaded
so that Kivy's rule-parser can resolve them by name.
"""
import logging

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.app import MDApp

from database import DatabaseManager

logger = logging.getLogger(__name__)


class EJiroApp(MDApp):
    """Main application class."""
    business_name = StringProperty("e-Jiro")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = DatabaseManager()
        self.business_name = self.database.get_setting("business_name", "e-Jiro")

    def build(self):
        # ── Register all custom classes with Kivy BEFORE loading the KV ──────
        # Widgets
        from app.widgets.header_bar import HeaderBar, RootWidget  # noqa: F401
        from app.widgets.stat_card import StatCard  # noqa: F401
        from app.widgets.list_items import (  # noqa: F401
            ClientListItem,
            LampListItem,
            LoanListItem,
            LoanListItemWithSelect,
            TransactionListItem,
        )
        from app.widgets.payment_items import (  # noqa: F401
            ClientPaymentItem,
            DailyPaymentListItem,
        )
        # Screens
        from app.screens.dashboard import DashboardScreen  # noqa: F401
        from app.screens.clients import ClientFormModal, ClientsScreen  # noqa: F401
        from app.screens.inventory import LampFormModal, InventoryScreen  # noqa: F401
        from app.screens.loan import LoanFormModal, LoanScreen  # noqa: F401
        from app.screens.payment import FolderChooserPopup, PaymentScreen  # noqa: F401
        from app.screens.history import HistoryScreen  # noqa: F401

        Builder.load_file("style.kv")
        return RootWidget()
