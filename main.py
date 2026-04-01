import logging
from datetime import datetime, date
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.metrics import sp
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.pickers import MDDatePicker

from database import DatabaseManager
from pdf_generator import generate_payment_report

logger = logging.getLogger(__name__)

DAY_COLORS = {
    0: (0.3, 0.7, 0.3, 1),  # Monday - Green
    1: (0.1, 0.5, 0.8, 1),  # Tuesday - Blue
    2: (0.6, 0.3, 0.8, 1),  # Wednesday - Purple
    3: (1.0, 0.6, 0.2, 1),  # Thursday - Orange
    4: (0.0, 0.6, 0.6, 1),  # Friday - Teal
    5: (0.9, 0.8, 0.2, 1),  # Saturday - Yellow
    6: (0.8, 0.3, 0.3, 1),  # Sunday - Red
}


class HeaderBar(BoxLayout):
    pass


class RootWidget(BoxLayout):
    def reload_app(self):
        app = App.get_running_app()
        app.database = DatabaseManager()
        self.ids.screen_manager.current = "dashboard"

    def exit_app(self):
        App.get_running_app().stop()

    def toggle_nav_drawer(self):
        drawer = self.ids.nav_drawer
        if drawer.state == "open":
            drawer.set_state("close")
        else:
            drawer.set_state("open")

    def refresh_history(self):
        logger.info("refresh_history called")
        history_screen = self.ids.screen_manager.get_screen("history")
        if hasattr(history_screen, "refresh_history"):
            logger.info("Calling history refresh_history")
            Clock.schedule_once(lambda dt: history_screen.refresh_history())
        else:
            logger.warning("history screen has no refresh_history")

    def force_refresh_history(self):
        logger.info("force_refresh_history called")
        try:
            history_screen = self.ids.screen_manager.get_screen("history")
            history_screen.refresh_history()
            logger.info("History refreshed successfully")
        except Exception as e:
            logger.error(f"Error force refreshing history: {e}")


def get_sp(size_name: str) -> int:
    sizes = {
        "header": sp(24),
        "title": sp(20),
        "body": sp(16),
        "button": sp(14),
    }
    return sizes.get(size_name, sp(16))


def is_mobile() -> bool:
    from kivy.metrics import Metrics

    return Metrics.platform in ("android", "ios") or Metrics.dpi < 200


class ClientListItem(ButtonBehavior, BoxLayout):
    client_name = StringProperty()
    client_telephone = StringProperty()
    client_adresse = StringProperty()
    client_id = None


class LampListItem(ButtonBehavior, BoxLayout):
    lamp_numero = StringProperty()
    lamp_etat = StringProperty()
    lamp_id = None


class LoanListItem(BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    loan_id = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class LoanListItemWithSelect(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    loan_id = None


class ClientPaymentItem(ButtonBehavior, BoxLayout):
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


class TransactionListItem(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    date_paiement = StringProperty()
    montant = StringProperty()
    day_color = ListProperty([0.5, 0.5, 0.5, 1])
    transaction_id = None


class StatCard(MDCard, ButtonBehavior):
    title = StringProperty()
    value = StringProperty()
    icon = StringProperty()


class FolderChooserPopup(Popup):
    initial_path = StringProperty("")
    
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.initial_path = self._get_initial_path()

    def _get_initial_path(self):
        import os
        # Try Downloads, then Home
        paths = [
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Téléchargements"),
            os.path.expanduser("~")
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return os.getcwd()

    def select_folder(self, path):
        if self.callback:
            self.callback(path)
        self.dismiss()


class DailyPaymentListItem(BoxLayout):
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


class LampFormModal(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inventory_screen = None
        self.mode = "add"
        self.selected_lamp_id = None
        self.numero_input = None
        self.etat_spinner = None
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
            text="Nouvelle Lampe",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height="40dp",
            theme_text_color="Custom",
            text_color=(0, 0, 0, 1),
        )
        card.add_widget(self.form_title)

        self.numero_input = MDTextField(
            hint_text="Numéro de lampe",
            mode="rectangle",
            size_hint_y=None,
            height="48dp",
        )
        card.add_widget(self.numero_input)

        from kivy.uix.spinner import Spinner

        self.etat_spinner = Spinner(
            text="disponible",
            values=("disponible", "louée", "maintenance"),
            size_hint_y=None,
            height="48dp",
        )
        card.add_widget(self.etat_spinner)

        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        self.save_button = MDRaisedButton(text="Ajouter", on_press=self.save_from_modal)
        cancel_button = MDRaisedButton(text="Annuler", on_press=self.dismiss)
        btn_layout.add_widget(self.save_button)
        btn_layout.add_widget(cancel_button)
        card.add_widget(btn_layout)

        self.add_widget(card)

    def open(self, inventory_screen, mode="add", lamp=None):
        self.inventory_screen = inventory_screen
        self.mode = mode
        if mode == "edit" and lamp:
            self.selected_lamp_id = lamp["id"]
            self.numero_input.text = lamp["numero"]
            self.etat_spinner.text = lamp["etat"]
            self.form_title.text = "Modifier Lampe"
            self.save_button.text = "Modifier"
        else:
            self.selected_lamp_id = None
            self.numero_input.text = ""
            self.etat_spinner.text = "disponible"
            self.form_title.text = "Nouvelle Lampe"
            self.save_button.text = "Ajouter"
        super().open()

    def save_from_modal(self, *args):
        numero = self.numero_input.text.strip()
        etat = self.etat_spinner.text

        if not numero:
            logger.warning("Numéro de lampe requis")
            return

        db = get_database()
        try:
            if self.mode == "edit" and self.selected_lamp_id:
                db.update_lamp(self.selected_lamp_id, numero, etat)
                logger.info(f"Lampe modifiée: {numero}")
            else:
                db.add_lamp_with_etat(numero, etat)
                logger.info(f"Lampe ajoutée: {numero}")
            self.inventory_screen.refresh_inventory()
            self.dismiss()
        except Exception as e:
            logger.error(f"Erreur: {e}")

    def dismiss(self, *args):
        super().dismiss()


def get_database() -> DatabaseManager:
    return App.get_running_app().database


class DashboardScreen(MDScreen):
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

        # Update labels if they exist (for backward compatibility with old layout)
        if hasattr(self.ids, "daily_label"):
            self.ids.daily_label.text = f"Journalier: {daily:.2f} AR"
        if hasattr(self.ids, "weekly_label"):
            self.ids.weekly_label.text = f"Hebdomadaire: {weekly:.2f} AR"


class ClientFormModal(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clients_screen = None
        self.mode = "add"
        self.selected_client_id = None
        self.nom_input = None
        self.telephone_input = None
        self.adresse_input = None
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
            text="Nouveau Client",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height="40dp",
            theme_text_color="Custom",
            text_color=(0, 0, 0, 1),
        )
        card.add_widget(self.form_title)

        self.nom_input = MDTextField(
            hint_text="Nom complet", mode="rectangle", size_hint_y=None, height="48dp"
        )
        card.add_widget(self.nom_input)

        self.telephone_input = MDTextField(
            hint_text="Téléphone", mode="rectangle", size_hint_y=None, height="48dp"
        )
        card.add_widget(self.telephone_input)

        self.adresse_input = MDTextField(
            hint_text="Adresse", mode="rectangle", size_hint_y=None, height="48dp"
        )
        card.add_widget(self.adresse_input)

        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        self.save_button = MDRaisedButton(text="Ajouter", on_press=self.save_from_modal)
        cancel_button = MDRaisedButton(text="Annuler", on_press=self.dismiss)
        btn_layout.add_widget(self.save_button)
        btn_layout.add_widget(cancel_button)
        card.add_widget(btn_layout)

        self.add_widget(card)

    def open(self, clients_screen, mode="add", client=None):
        self.clients_screen = clients_screen
        self.mode = mode
        if mode == "edit" and client:
            self.selected_client_id = client["id"]
            self.nom_input.text = client["nom"]
            self.telephone_input.text = client["telephone"]
            self.adresse_input.text = client["adresse"] or ""
            self.form_title.text = "Modifier Client"
            self.save_button.text = "Modifier"
        else:
            self.selected_client_id = None
            self.nom_input.text = ""
            self.telephone_input.text = ""
            self.adresse_input.text = ""
            self.form_title.text = "Nouveau Client"
            self.save_button.text = "Ajouter"
        super().open()

    def save_from_modal(self, *args):
        nom = self.nom_input.text.strip()
        telephone = self.telephone_input.text.strip()
        adresse = self.adresse_input.text.strip()

        if not nom or not telephone:
            logger.warning("Nom et téléphone requis")
            return

        db = get_database()
        try:
            if self.mode == "edit" and self.selected_client_id:
                db.update_client(self.selected_client_id, nom, telephone, adresse)
                logger.info(f"Client modifié: {nom}")
            else:
                db.add_client(nom, telephone, adresse)
                logger.info(f"Client ajouté: {nom}")
            self.clients_screen.refresh_clients()
            self.dismiss()
        except Exception as e:
            logger.error(f"Erreur: {e}")

    def dismiss(self, *args):
        super().dismiss()


class ClientsScreen(MDScreen):
    selected_client_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_clients())
        self.modal = ClientFormModal()

    def show_client_form(self, mode):
        try:
            if mode == "edit":
                if not self.selected_client_id:
                    logger.warning("Aucun client sélectionné")
                    return
                client = get_database().get_client_by_id(self.selected_client_id)
                if not client:
                    logger.warning("Client non trouvé")
                    return
                self.modal.open(self, "edit", client)
            else:
                self.modal.open(self, "add")
        except Exception as e:
            logger.error(f"Erreur show_client_form: {e}")

    def refresh_clients(self, query=None):
        db = get_database()
        clients = db.get_all_clients(query=query)
        self.ids.clients_list.clear_widgets()
        for c in clients:
            item = ClientListItem(
                client_name=c["nom"],
                client_telephone=c["telephone"],
                client_adresse=c["adresse"] or "Pas d'adresse",
            )
            item.client_id = c["id"]
            item.bind(on_press=lambda instance: self.select_client(instance.client_id))
            self.ids.clients_list.add_widget(item)
        self.selected_client_id = None

    def select_client(self, client_id):
        self.selected_client_id = client_id
        logger.info(f"Client sélectionné: {client_id}")

    def delete_client(self):
        if not self.selected_client_id:
            logger.warning("Aucun client sélectionné")
            return
        self.show_delete_confirmation()

    def show_delete_confirmation(self):
        content = BoxLayout(orientation="vertical", padding="24dp", spacing="16dp")
        content.add_widget(
            MDLabel(text="Voulez-vous vraiment\nsupprimer ce client?", halign="center")
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
            get_database().delete_client(self.selected_client_id)
            logger.info("Client supprimé")
            self.refresh_clients()
        except Exception as e:
            logger.error(f"Erreur: {e}")
        self.delete_popup.dismiss()

    def cancel_delete(self, *args):
        self.delete_popup.dismiss()


class InventoryScreen(MDScreen):
    selected_lamp_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_inventory())
        self.modal = LampFormModal()

    def refresh_inventory(self, query=None):
        db = get_database()
        lamps = db.get_all_lamps(query=query)
        self.ids.inventory_list.clear_widgets()
        for lamp in lamps:
            item = LampListItem(
                lamp_numero=lamp["numero"],
                lamp_etat=lamp["etat"],
            )
            item.lamp_id = lamp["id"]
            item.bind(on_press=lambda instance, lid=lamp["id"]: self.select_lamp(lid))
            self.ids.inventory_list.add_widget(item)
        self.selected_lamp_id = None

    def select_lamp(self, lamp_id):
        self.selected_lamp_id = lamp_id
        logger.info(f"Lampe sélectionnée: {lamp_id}")

    def show_lamp_form(self, mode):
        try:
            if mode == "edit":
                if not self.selected_lamp_id:
                    logger.warning("Aucune lampe sélectionnée")
                    return
                lamp = get_database().get_lamp_by_id(self.selected_lamp_id)
                if not lamp:
                    logger.warning("Lampe non trouvée")
                    return
                self.modal.open(self, "edit", lamp)
            else:
                self.modal.open(self, "add")
        except Exception as e:
            logger.error(f"Erreur show_lamp_form: {e}")

    def delete_lamp(self):
        if not self.selected_lamp_id:
            logger.warning("Aucune lampe sélectionnée")
            return
        self.show_delete_confirmation()

    def show_delete_confirmation(self):
        content = BoxLayout(orientation="vertical", padding="24dp", spacing="16dp")
        content.add_widget(
            MDLabel(
                text="Voulez-vous vraiment\nsupprimer cette lampe?", halign="center"
            )
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
            get_database().delete_lamp(self.selected_lamp_id)
            logger.info("Lampe supprimée")
            self.refresh_inventory()
        except Exception as e:
            logger.error(f"Erreur: {e}")
        self.delete_popup.dismiss()

    def cancel_delete(self, *args):
        self.delete_popup.dismiss()


class LoanFormModal(Popup):
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

        from kivy.uix.spinner import Spinner

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

        # Populate clients
        clients = db.get_all_clients()
        self.client_spinner.values = [c["nom"] for c in clients]
        self.client_spinner.text = "Sélectionner Client"

        # Populate available lamps
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

        if client_nom == "Sélectionner Client" or lampe_numero == "Sélectionner Lampe":
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
    selected_loan_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_data())
        Clock.schedule_once(lambda dt: self.refresh_loans())

    def show_loan_form(self, *args):
        # We might not need this anymore if we are using on-screen creation
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
        
        # Pre-fill default rate
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


class PaymentScreen(MDScreen):
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
        # Redirect to refresh_clients for consistency
        self.refresh_clients()

    def update_totals(self):
        # Already handled by refresh_total elsewhere or partially here
        self.refresh_total()

    def show_date_picker(self):
        date_dialog = MDDatePicker()
        if self.selected_date:
            try:
                # Expecting YYYY-MM-DD
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
        
        # Open folder picker first
        popup = FolderChooserPopup(callback=self._on_folder_selected)
        popup.open()

    def _on_folder_selected(self, output_dir):
        db = get_database()
        data = db.get_payments_by_date(self.selected_date)
        
        try:
            app = MDApp.get_running_app()
            business_name = app.business_name if hasattr(app, "business_name") else "e-Jiro"
            filename = generate_payment_report(
                self.selected_date, 
                data, 
                business_name=business_name,
                output_dir=output_dir
            )
            # Show success message
            self.show_success_dialog(filename)
            logger.info(f"Report generated: {filename}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

    def show_success_dialog(self, filepath):
        content = BoxLayout(orientation="vertical", padding="12dp", spacing="12dp")
        content.add_widget(MDLabel(
            text=f"Le rapport a été enregistré avec succès dans :\n\n{filepath}",
            halign="center"
        ))
        btn = MDRaisedButton(
            text="OK",
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self.success_dialog.dismiss()
        )
        content.add_widget(btn)
        
        from kivy.uix.popup import Popup
        self.success_dialog = Popup(
            title="Succès",
            content=content,
            size_hint=(0.8, 0.4)
        )
        self.success_dialog.open()

class HistoryScreen(MDScreen):
    selected_date = StringProperty("")
    total_filtered_amount = StringProperty("0 Ar")
    paid_count = StringProperty("0")
    unpaid_count = StringProperty("0")

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_history())

    def on_selected_date(self, instance, value):
        if hasattr(self.ids, "date_filter_label"):
            self.ids.date_filter_label.text = f"Date: {value}" if value else "Tous les paiements"
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
            # Calculate stats for the selected date
            payments = db.get_payments_by_date(self.selected_date)
            self.paid_count = str(sum(1 for p in payments if p["is_paid"]))
            self.unpaid_count = str(sum(1 for p in payments if not p["is_paid"]))
        else:
            transactions = db.get_all_transactions()
            # If no date selected, maybe show stats for today
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
                # Get color based on day of week (0=Monday)
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
                day_color=d_color
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
            MDLabel(text="Voulez-vous vraiment\nsupprimer tout l'historique?", halign="center")
        )
        btn_layout = BoxLayout(size_hint_y=None, height="48dp", spacing="12dp")
        btn_confirm = MDRaisedButton(
            text="Oui, Tout Effacer", 
            on_press=self.confirm_clear_history,
            md_bg_color=(0.9, 0.3, 0.3, 1)
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
            # Also refresh dashboard stats
            app = MDApp.get_running_app()
            dashboard_screen = app.root.ids.screen_manager.get_screen("dashboard")
            dashboard_screen.update_stats()
        except Exception as e:
            logger.error(f"Error: {e}")
        self.clear_popup.dismiss()

    def cancel_clear(self, *args):
        self.clear_popup.dismiss()

    def filter_transactions(self, query=None):
        # We can implement specific filtering logic here if needed
        # For now, refresh_history handles the date filter
        self.refresh_history()


class EJiroApp(MDApp):
    business_name = StringProperty("e-Jiro")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = DatabaseManager()
        self.business_name = self.database.get_setting("business_name", "e-Jiro")

    def build(self):
        Builder.load_file("style.kv")
        return RootWidget()


if __name__ == "__main__":
    EJiroApp().run()
