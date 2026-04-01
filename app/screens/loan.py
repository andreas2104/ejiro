"""
app/screens/loan.py — LoanFormModal popup and LoanScreen.
"""
import logging

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from app.utils import get_database
from app.widgets.list_items import LoanListItemWithSelect

logger = logging.getLogger(__name__)


class LoanFormModal(Popup):
    """Modal dialog for creating a new loan."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loan_screen = None
        self.client_spinner = None
        self.lampe_spinner = None
        self.montant_input = None
        self.form_title = None
        self.save_button = None
        self._build_ui()

    def _build_ui(self):
        card = MDCard(
            orientation="vertical",
            padding="24dp",
            spacing="16dp",
            md_bg_color=(1, 1, 1, 1),
        )

        self.form_title = MDLabel(
            text="Nouveau Prêt",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height="40dp",
            theme_text_color="Custom",
            text_color=(0, 0, 0, 1),
        )
        card.add_widget(self.form_title)

        self.client_spinner = Spinner(
            text="Sélectionner Client",
            values=[],
            size_hint_y=None,
            height="48dp",
        )
        card.add_widget(self.client_spinner)

        self.lampe_spinner = Spinner(
            text="Sélectionner Lampe",
            values=[],
            size_hint_y=None,
            height="48dp",
        )
        card.add_widget(self.lampe_spinner)

        self.montant_input = MDTextField(
            hint_text="Montant journalier (Ar)",
            mode="rectangle",
            size_hint_y=None,
            height="48dp",
            input_filter="float",
        )
        card.add_widget(self.montant_input)

        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        self.save_button = MDRaisedButton(text="Ajouter", on_press=self.save_from_modal)
        cancel_button = MDRaisedButton(text="Annuler", on_press=self.dismiss)
        btn_layout.add_widget(self.save_button)
        btn_layout.add_widget(cancel_button)
        card.add_widget(btn_layout)

        self.add_widget(card)

    def open(self, loan_screen):
        self.loan_screen = loan_screen
        db = get_database()

        clients = db.get_all_clients()
        self.client_spinner.values = [c["nom"] for c in clients]
        self.client_spinner.text = "Sélectionner Client"

        available_lamps = [
            lamp for lamp in db.get_all_lamps() if lamp["etat"] == "disponible"
        ]
        self.lampe_spinner.values = [lamp["numero"] for lamp in available_lamps]
        self.lampe_spinner.text = "Sélectionner Lampe"

        self.montant_input.text = ""
        super().open()

    def save_from_modal(self, *args):
        client_nom = self.client_spinner.text
        lampe_numero = self.lampe_spinner.text
        montant_text = self.montant_input.text.strip()

        if (
            client_nom == "Sélectionner Client"
            or lampe_numero == "Sélectionner Lampe"
        ):
            logger.warning("Veuillez sélectionner un client et une lampe")
            return

        try:
            montant_journalier = float(montant_text) if montant_text else 0
        except ValueError:
            logger.warning("Montant invalide")
            return

        if montant_journalier <= 0:
            logger.warning("Le montant doit être positif")
            return

        db = get_database()
        clients = db.get_all_clients()
        client = next((c for c in clients if c["nom"] == client_nom), None)
        lampe = next(
            (lamp for lamp in db.get_all_lamps() if lamp["numero"] == lampe_numero),
            None,
        )

        if not client or not lampe:
            logger.warning("Données invalides")
            return

        try:
            db.assign_lamps_to_client(client["id"], lampe["id"], montant_journalier)
            logger.info(f"Prêt créé: {montant_journalier}/jour")
            self.loan_screen.refresh_loans()
            self.dismiss()
        except Exception as e:
            logger.error(f"Erreur: {e}")

    def dismiss(self, *args):
        super().dismiss()


class LoanScreen(MDScreen):
    """Screen for creating and managing active loans."""
    selected_loan_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_data())
        Clock.schedule_once(lambda dt: self.refresh_loans())

    def show_loan_form(self, *args):
        # On-screen creation is used; modal kept for compat
        pass

    def load_data(self):
        db = get_database()
        clients = db.get_all_clients()
        if hasattr(self.ids, "client_spinner"):
            self.ids.client_spinner.values = [c["nom"] for c in clients]
        available_lamps = [
            lamp for lamp in db.get_all_lamps() if lamp["etat"] == "disponible"
        ]
        if hasattr(self.ids, "lampe_spinner"):
            self.ids.lampe_spinner.values = [lamp["numero"] for lamp in available_lamps]
        if hasattr(self.ids, "montant_input"):
            default_rate = db.get_setting("default_rate", "1000")
            self.ids.montant_input.text = default_rate

    def refresh_loans(self, query=None):
        db = get_database()
        loans = db.get_all_loans(query=query)
        self.ids.loans_list.clear_widgets()
        for loan in loans:
            item = LoanListItemWithSelect(
                client_nom=loan["client_nom"],
                lampe_numero=loan["lamps_numero"],
                montant_journalier=f"{loan['montant_journalier']:.0f}",
            )
            item.loan_id = loan["id"]
            item.bind(on_press=lambda inst: self.select_loan(inst.loan_id))
            self.ids.loans_list.add_widget(item)
        self.selected_loan_id = None

    def select_loan(self, loan_id):
        self.selected_loan_id = loan_id
        logger.info(f"Prêt sélectionné: {loan_id}")

    def assign_lampe(self, client_nom: str, lampe_numero: str, montant_text: str):
        try:
            montant_journalier = float(montant_text) if montant_text else 0
        except ValueError:
            logger.warning("Montant invalide")
            return

        if montant_journalier <= 0:
            logger.warning("Le montant doit être positif")
            return

        db = get_database()
        clients = db.get_all_clients()
        client = next((c for c in clients if c["nom"] == client_nom), None)
        if not client:
            logger.warning("Client non trouvé")
            return

        lampe = next(
            (lamp for lamp in db.get_all_lamps() if lamp["numero"] == lampe_numero),
            None,
        )
        if not lampe:
            logger.warning("Lampe non trouvée")
            return

        try:
            db.assign_lamps_to_client(client["id"], lampe["id"], montant_journalier)
            logger.info(f"Prêt créé: {montant_journalier}/jour")
            self.refresh_loans()
            self.load_data()
        except Exception as e:
            logger.error(f"Erreur: {e}")

    def close_loan(self):
        if not self.selected_loan_id:
            logger.warning("Aucun prêt sélectionné")
            return
        self.show_close_confirmation()

    def show_close_confirmation(self):
        content = BoxLayout(orientation="vertical", padding="24dp", spacing="16dp")
        content.add_widget(
            MDLabel(text="Voulez-vous vraiment\nclore ce prêt?", halign="center")
        )
        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        btn_confirm = MDRaisedButton(text="Oui, clore", on_press=self.confirm_close)
        btn_cancel = MDRaisedButton(text="Annuler", on_press=self.cancel_close)
        btn_layout.add_widget(btn_confirm)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        self.close_popup = Popup(
            title="Confirmer clôture",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
        )
        self.close_popup.open()

    def confirm_close(self, *args):
        try:
            get_database().close_loan(self.selected_loan_id)
            logger.info("Prêt clos")
            self.refresh_loans()
            self.load_data()
        except Exception as e:
            logger.error(f"Erreur: {e}")
        self.close_popup.dismiss()

    def cancel_close(self, *args):
        self.close_popup.dismiss()

    def delete_loan(self):
        if not self.selected_loan_id:
            logger.warning("Aucun prêt sélectionné")
            return
        self.show_delete_confirmation()

    def show_delete_confirmation(self):
        content = BoxLayout(orientation="vertical", padding="24dp", spacing="16dp")
        content.add_widget(
            MDLabel(text="Voulez-vous vraiment\nsupprimer ce prêt?", halign="center")
        )
        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        btn_confirm = MDRaisedButton(
            text="Oui, supprimer", on_press=self.confirm_delete
        )
        btn_cancel = MDRaisedButton(text="Annuler", on_press=self.cancel_delete)
        btn_layout.add_widget(btn_confirm)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        self.delete_popup = Popup(
            title="Confirmer suppression",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
        )
        self.delete_popup.open()

    def confirm_delete(self, *args):
        try:
            get_database().delete_loan(self.selected_loan_id)
            logger.info("Prêt supprimé")
            self.refresh_loans()
            self.load_data()
        except Exception as e:
            logger.error(f"Erreur: {e}")
        self.delete_popup.dismiss()

    def cancel_delete(self, *args):
        self.delete_popup.dismiss()
