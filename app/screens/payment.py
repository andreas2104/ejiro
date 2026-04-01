"""
app/screens/payment.py — FolderChooserPopup and PaymentScreen.
"""
import logging
import os
from datetime import datetime

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen

from app.utils import get_database
from app.widgets.payment_items import ClientPaymentItem
from pdf_generator import generate_payment_report

logger = logging.getLogger(__name__)


class FolderChooserPopup(Popup):
    """Popup for selecting an output folder for the PDF report."""
    initial_path = StringProperty("")

    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.initial_path = self._get_initial_path()

    def _get_initial_path(self):
        paths = [
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Téléchargements"),
            os.path.expanduser("~"),
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return os.getcwd()

    def select_folder(self, path):
        if self.callback:
            self.callback(path)
        self.dismiss()


class PaymentScreen(MDScreen):
    """Screen for tracking daily payment status per client/lamp."""
    selected_date = StringProperty("")

    def on_enter(self):
        if not self.selected_date:
            self.selected_date = datetime.now().date().isoformat()
        Clock.schedule_once(lambda dt: self.refresh_clients())

    def on_selected_date(self, instance, value):
        if hasattr(self.ids, "date_label"):
            self.ids.date_label.text = f"Date: {value}"
        Clock.schedule_once(lambda dt: self.refresh_clients())

    def refresh_daily_payments(self):
        self.refresh_clients()

    def update_totals(self):
        self.refresh_total()

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        if self.selected_date:
            try:
                d = datetime.strptime(self.selected_date, "%Y-%m-%d")
                date_dialog.year = d.year
                date_dialog.month = d.month
                date_dialog.day = d.day
            except Exception as e:
                logger.error(f"Error parsing date: {e}")
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()

    def on_date_save(self, instance, value, date_range):
        self.selected_date = value.isoformat()

    def refresh_clients(self):
        db = get_database()
        if not self.selected_date:
            self.selected_date = datetime.now().date().isoformat()

        data = db.get_payments_by_date(self.selected_date)
        self.ids.loans_list.clear_widgets()

        day_total = 0
        for client in data:
            for lamp in client["lamps"]:
                item = ClientPaymentItem(
                    client_nom=client["client_nom"],
                    client_telephone=client["client_telephone"],
                    client_adresse=client["client_adresse"] or "Pas d'adresse",
                    lamps_info=f"Lampe {lamp['numero']}",
                    is_paid=lamp["is_paid"],
                )
                item.client_id = client["client_id"]
                item.pret_id = lamp["pret_id"]
                item.client_data = lamp
                self.ids.loans_list.add_widget(item)
                if lamp["is_paid"]:
                    day_total += lamp["montant"]

        self.ids.total_label.text = f"Total: {day_total:.0f} Ar"

    def on_client_paid_toggle(self, item, is_paid):
        db = get_database()
        try:
            db.toggle_payment(
                item.pret_id,
                self.selected_date,
                float(item.client_data["montant"]),
                is_paid,
            )
            logger.info(f"Payment toggled for loan {item.pret_id}: {is_paid}")
            self.refresh_total()
        except Exception as e:
            logger.error(f"Error toggling payment: {e}")

    def refresh_total(self):
        db = get_database()
        data = db.get_payments_by_date(self.selected_date)
        day_total = 0
        for client in data:
            for lamp in client["lamps"]:
                if lamp["is_paid"]:
                    day_total += lamp["montant"]
        self.ids.total_label.text = f"Total: {day_total:.0f} Ar"

    def generate_pdf_report(self):
        db = get_database()
        data = db.get_payments_by_date(self.selected_date)
        if not data:
            logger.warning("No data found for the selected date")
            return
        popup = FolderChooserPopup(callback=self._on_folder_selected)
        popup.open()

    def _on_folder_selected(self, output_dir):
        db = get_database()
        data = db.get_payments_by_date(self.selected_date)
        try:
            app = MDApp.get_running_app()
            business_name = (
                app.business_name if hasattr(app, "business_name") else "e-Jiro"
            )
            filename = generate_payment_report(
                self.selected_date,
                data,
                business_name=business_name,
                output_dir=output_dir,
            )
            self.show_success_dialog(filename)
            logger.info(f"Report generated: {filename}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    def show_success_dialog(self, filepath):
        content = BoxLayout(orientation="vertical", padding="12dp", spacing="12dp")
        content.add_widget(
            MDLabel(
                text=f"Le rapport a été enregistré avec succès dans :\n\n{filepath}",
                halign="center",
            )
        )
        btn = MDRaisedButton(
            text="OK",
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self.success_dialog.dismiss(),
        )
        content.add_widget(btn)
        self.success_dialog = Popup(
            title="Succès",
            content=content,
            size_hint=(0.8, 0.4),
        )
        self.success_dialog.open()
