"""
app/screens/dashboard.py — DashboardScreen.
"""
import logging

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from app.utils import get_database

logger = logging.getLogger(__name__)


class DashboardScreen(MDScreen):
    """Home screen showing global stats (clients, lamps, loans, revenue)."""
    client_count = StringProperty("0")
    lamp_count = StringProperty("0")
    loan_count = StringProperty("0")
    daily_revenue = StringProperty("0 Ar")
    total_revenue = StringProperty("0 Ar")

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.update_stats())

    def update_stats(self):
        db = get_database()
        daily = db.get_daily_revenue()
        total = db.get_total_revenue()
        weekly = db.get_weekly_revenue()
        client_count = db.get_clients_count()
        lamp_count = db.get_lamps_count()
        loan_count = db.get_active_loans_count()

        self.client_count = str(client_count)
        self.lamp_count = str(lamp_count)
        self.loan_count = str(loan_count)
        self.daily_revenue = f"{daily:.0f} Ar"
        self.total_revenue = f"{total:.0f} Ar"

        # Backward-compat: if old KV ids still present
        if hasattr(self.ids, "daily_label"):
            self.ids.daily_label.text = f"Journalier: {daily:.2f} AR"
        if hasattr(self.ids, "weekly_label"):
            self.ids.weekly_label.text = f"Hebdomadaire: {weekly:.2f} AR"
