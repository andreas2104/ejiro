import logging
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
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

from database import DatabaseManager

logger = logging.getLogger(__name__)


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


class LoanListItem(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    montant_journalier = StringProperty()
    is_paid = BooleanProperty(False)
    loan_id = None
    loan_data = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_paid_toggle")

    def on_paid_toggle(self, *args):
        pass


class TransactionListItem(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    date_paiement = StringProperty()
    montant = StringProperty()
    transaction_id = None


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
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.update_revenue())

    def update_revenue(self):
        db = get_database()
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()
        self.ids.daily_label.text = f"Journalier: {daily:.2f} CFA"
        self.ids.weekly_label.text = f"Hebdomadaire: {weekly:.2f} CFA"


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

    def refresh_clients(self):
        db = get_database()
        clients = db.get_all_clients()
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

    def refresh_inventory(self):
        db = get_database()
        lamps = db.get_all_lamps()
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


class LoanScreen(MDScreen):
    selected_loan_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_data())
        Clock.schedule_once(lambda dt: self.refresh_loans())

    def load_data(self):
        db = get_database()
        clients = db.get_all_clients()
        self.ids.client_spinner.values = [c["nom"] for c in clients]
        available_lamps = [
            lamp for lamp in db.get_all_lamps() if lamp["etat"] == "disponible"
        ]
        self.ids.lampe_spinner.values = [lamp["numero"] for lamp in available_lamps]

    def refresh_loans(self):
        db = get_database()
        loans = db.get_all_loans()
        self.ids.loans_list.clear_widgets()
        for loan in loans:
            item = LoanListItem(
                client_nom=loan["client_nom"],
                lampe_numero=loan["lampe_numero"],
                date_debut=loan["date_debut"][:10],
                statut=loan["statut"],
            )
            item.loan_id = loan["id"]
            item.bind(on_press=lambda instance: self.select_loan(instance.loan_id))
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
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_loans())

    def refresh_loans(self):
        db = get_database()
        unpaid_loans = db.get_unpaid_loans_today()
        self.ids.loans_list.clear_widgets()

        today = datetime.now().date().isoformat()

        for loan in unpaid_loans:
            item = LoanListItem(
                client_nom=loan["client_nom"],
                lampe_numero=loan["lamps_numero"],
                montant_journalier=f"{loan['montant_journalier']:.0f}",
                is_paid=False,
            )
            item.loan_id = loan["id"]
            item.loan_data = loan
            item.bind(on_paid_toggle=self.on_loan_paid_toggle)
            self.ids.loans_list.add_widget(item)

        self.update_summary()

    def on_loan_paid_toggle(self, instance, value):
        if value and instance.loan_data:
            db = get_database()
            try:
                db.record_payment(
                    instance.loan_id, instance.loan_data["montant_journalier"]
                )
                logger.info(f"Paiement enregistré pour prêt {instance.loan_id}")
                self.refresh_loans()
            except Exception as e:
                logger.error(f"Erreur: {e}")

    def mark_all_paid(self):
        db = get_database()
        unpaid_loans = db.get_unpaid_loans_today()

        for loan in unpaid_loans:
            try:
                db.record_payment(loan["id"], loan["montant_journalier"])
            except Exception as e:
                logger.error(f"Erreur pour prêt {loan['id']}: {e}")

        self.refresh_loans()

    def update_summary(self):
        db = get_database()
        unpaid = db.get_unpaid_loans_today()
        total_due = sum(loan["montant_journalier"] for loan in unpaid)
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()

        if hasattr(self.ids, "daily_label"):
            self.ids.daily_label.text = f"Jour: {daily:.0f} CFA"
        if hasattr(self.ids, "weekly_label"):
            self.ids.weekly_label.text = f"Semaine: {weekly:.0f} CFA"


class LampManagerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = DatabaseManager()

    def build(self):
        Builder.load_file("style.kv")
        return RootWidget()


if __name__ == "__main__":
    LampManagerApp().run()
