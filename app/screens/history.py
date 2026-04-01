"""
app/screens/history.py — HistoryScreen.
"""
import logging
from datetime import datetime, date

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from app.utils import get_database, DAY_COLORS
from app.widgets.list_items import TransactionListItem

logger = logging.getLogger(__name__)


class HistoryScreen(MDScreen):
    """Screen showing all historical payment transactions with date filter."""
    selected_date = StringProperty("")
    total_filtered_amount = StringProperty("0 Ar")
    paid_count = StringProperty("0")
    unpaid_count = StringProperty("0")

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_history())

    def on_selected_date(self, instance, value):
        if hasattr(self.ids, "date_filter_label"):
            self.ids.date_filter_label.text = (
                f"Date: {value}" if value else "Tous les paiements"
            )
        Clock.schedule_once(lambda dt: self.refresh_history())

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        if self.selected_date:
            try:
                d = datetime.strptime(self.selected_date, "%Y-%m-%d")
                date_dialog.year = d.year
                date_dialog.month = d.month
                date_dialog.day = d.day
            except Exception:
                pass
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        self.selected_date = value.isoformat()

    def clear_filter(self):
        self.selected_date = ""

    def refresh_history(self):
        db = get_database()
        if self.selected_date:
            transactions = db.get_transactions_on_date(self.selected_date)
            payments = db.get_payments_by_date(self.selected_date)
            self.paid_count = str(sum(1 for p in payments if p["is_paid"]))
            self.unpaid_count = str(sum(1 for p in payments if not p["is_paid"]))
        else:
            transactions = db.get_all_transactions()
            today = date.today().isoformat()
            payments = db.get_payments_by_date(today)
            self.paid_count = str(sum(1 for p in payments if p["is_paid"]))
            self.unpaid_count = str(sum(1 for p in payments if not p["is_paid"]))

        self.ids.history_list.clear_widgets()
        total_sum = 0
        for t in transactions:
            try:
                dt = datetime.fromisoformat(t["date_paiement"])
                date_str = dt.strftime("%Y-%m-%d %H:%M")
                weekday = dt.weekday()
                d_color = DAY_COLORS.get(weekday, (0.5, 0.5, 0.5, 1))
            except Exception:
                date_str = t["date_paiement"][:16]
                d_color = (0.5, 0.5, 0.5, 1)

            item = TransactionListItem(
                client_nom=t["client_nom"],
                lampe_numero=t["lamps_numero"],
                date_paiement=date_str,
                montant=f"{t['montant']:.0f}",
                day_color=d_color,
            )
            item.transaction_id = t["id"]
            self.ids.history_list.add_widget(item)
            total_sum += t["montant"]

        self.total_filtered_amount = f"{total_sum:.0f} Ar"

    def update_totals(self):
        db = get_database()
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()
        monthly = db.get_monthly_revenue()

        if hasattr(self.ids, "daily_label"):
            self.ids.daily_label.text = f"Aujourd'hui: {daily:.0f} Ar"
        if hasattr(self.ids, "weekly_label"):
            self.ids.weekly_label.text = f"Semaine: {weekly:.0f} Ar"
        if hasattr(self.ids, "monthly_label"):
            self.ids.monthly_label.text = f"Mois: {monthly:.0f} Ar"
        if hasattr(self.ids, "current_date_label"):
            self.ids.current_date_label.text = (
                f"Historique - {date.today().strftime('%d/%m/%Y')}"
            )

    def show_clear_confirmation(self):
        content = BoxLayout(orientation="vertical", padding="24dp", spacing="16dp")
        content.add_widget(
            MDLabel(
                text="Voulez-vous vraiment\nsupprimer tout l'historique?",
                halign="center",
            )
        )
        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        btn_confirm = MDRaisedButton(
            text="Oui, Tout Effacer",
            on_press=self.confirm_clear_history,
            md_bg_color=(0.9, 0.3, 0.3, 1),
        )
        btn_cancel = MDRaisedButton(text="Annuler", on_press=self.cancel_clear)
        btn_layout.add_widget(btn_confirm)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        self.clear_popup = Popup(
            title="Confirmer suppression",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
        )
        self.clear_popup.open()

    def confirm_clear_history(self, *args):
        try:
            get_database().clear_all_transactions()
            logger.info("History cleared")
            self.refresh_history()
            app = MDApp.get_running_app()
            dashboard_screen = app.root.ids.screen_manager.get_screen("dashboard")
            dashboard_screen.update_stats()
        except Exception as e:
            logger.error(f"Error: {e}")
        self.clear_popup.dismiss()

    def cancel_clear(self, *args):
        self.clear_popup.dismiss()

    def filter_transactions(self, query=None):
        self.refresh_history()
