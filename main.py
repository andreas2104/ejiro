import logging
from datetime import date
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

    def refresh_history(self):
        logger.info("refresh_history called")
        history_screen = self.ids.screen_manager.get_screen("history")
        if hasattr(history_screen, "refresh_transactions"):
            logger.info("Calling history refresh_transactions")
            Clock.schedule_once(lambda dt: history_screen.refresh_transactions())
            Clock.schedule_once(lambda dt: history_screen.update_totals())
        else:
            logger.warning("history screen has no refresh_transactions")

    def force_refresh_history(self):
        logger.info("force_refresh_history called")
        try:
            history_screen = self.ids.screen_manager.get_screen("history")
            history_screen.refresh_transactions()
            history_screen.update_totals()
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


class LoanListItem(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    date_debut = StringProperty()
    statut = StringProperty()
    loan_id = None


class TransactionListItem(ButtonBehavior, BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    date_paiement = StringProperty()
    montant = StringProperty()
    transaction_id = None


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
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.update_revenue())

    def update_revenue(self):
        db = get_database()
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()
        self.ids.daily_label.text = f"Journalier: {daily:.2f} AR"
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

    def assign_lampe(
        self, client_nom: str, lampe_numero: str, montant_journalier: float
    ):
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
            db.assign_lampe_to_client(client["id"], lampe["id"], montant_journalier)
            logger.info("Prêt créé")
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
        self.current_payment_date = date.today().isoformat()
        self.pending_payments = []
        self.ids.current_date_label.text = (
            f"Paiements du {date.today().strftime('%d/%m/%Y')}"
        )
        self.refresh_daily_payments()

    def load_today_payments(self):
        self.current_payment_date = date.today().isoformat()
        self.ids.current_date_label.text = (
            f"Paiements du {date.today().strftime('%d/%m/%Y')}"
        )
        self.refresh_daily_payments()

    def go_back(self):
        from kivy.app import App

        app = App.get_running_app()
        root = app.root
        if hasattr(root, "ids") and hasattr(root.ids, "screen_manager"):
            root.ids.screen_manager.current = "dashboard"

    def get_current_date(self):
        from datetime import date

        return date.today().strftime("%d/%m/%Y")

    def load_today_payments(self):
        from datetime import date

        self.load_payments_for_date()

    def load_payments_for_date(self):
        from datetime import date

        self.current_payment_date = date.today().isoformat()
        self.ids.current_date_label.text = (
            f"Paiements du {date.today().strftime('%d/%m/%Y')}"
        )
        self.refresh_daily_payments()

    def refresh_daily_payments(self):
        if not self.current_payment_date:
            return

        try:
            db = get_database()
            active_loans = db.get_active_loans()

            if not hasattr(self, "ids") or not hasattr(self.ids, "daily_payments_list"):
                logger.warning("daily_payments_list not accessible")
                return

            self.ids.daily_payments_list.clear_widgets()
            self.pending_payments = []

            for loan in active_loans:
                item = DailyPaymentListItem(
                    client_nom=loan["client_nom"],
                    lampe_numero=loan["lampe_numero"],
                    montant_journalier=f"{loan['montant_journalier']:.2f}",
                    is_paid=False,
                )
                item.loan_id = loan["id"]
                item.montant_journalier_value = loan["montant_journalier"]
                item.bind(on_checkbox_active=self.on_payment_toggle)
                self.ids.daily_payments_list.add_widget(item)

            self.update_totals()
        except Exception as e:
            logger.error(f"Erreur dans refresh_daily_payments: {e}")

    def on_payment_toggle(self, instance, value):
        loan_id = instance.loan_id

        if value and loan_id not in self.pending_payments:
            self.pending_payments.append(loan_id)
        elif not value and loan_id in self.pending_payments:
            self.pending_payments.remove(loan_id)

        self.update_totals()

    def select_all_payments(self):
        if not self.current_payment_date:
            logger.warning("Aucune date sélectionnée")
            return

        self.pending_payments = []
        for widget in self.ids.daily_payments_list.children:
            if hasattr(widget, "loan_id"):
                self.pending_payments.append(widget.loan_id)

        for widget in self.ids.daily_payments_list.children:
            if hasattr(widget, "loan_id"):
                widget.is_paid = True

        self.update_totals()

    def save_payments(self):
        try:
            if not self.current_payment_date:
                logger.warning("Aucune date sélectionnée - Cliquez d'abord sur Charger")
                return

            if not self.pending_payments:
                logger.warning("Aucun paiement à sauvegarder")
                return

            db = get_database()
            saved_count = 0
            payments_to_save = list(self.pending_payments)

            for loan_id in payments_to_save:
                try:
                    montant = None
                    if hasattr(self, "ids") and hasattr(
                        self.ids, "daily_payments_list"
                    ):
                        for widget in self.ids.daily_payments_list.children:
                            if hasattr(widget, "loan_id") and widget.loan_id == loan_id:
                                if hasattr(widget, "montant_journalier_value"):
                                    montant = widget.montant_journalier_value
                                    break

                    if montant is None:
                        logger.warning(f"Montant non trouvé pour prêt {loan_id}")
                        continue

                    payment_date = f"{self.current_payment_date}T00:00:00"
                    logger.info(
                        f"Saving payment for loan {loan_id} with date: {payment_date}"
                    )
                    db.record_payment(loan_id, montant, date_paiement=payment_date)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Erreur pour prêt {loan_id}: {e}")
                    continue

            logger.info(f"Paiements sauvegardés: {saved_count}")
            self.pending_payments = []
            self.refresh_daily_payments()

            app = App.get_running_app()
            root = app.root
            root.force_refresh_history()
        except Exception as e:
            logger.error(f"Erreur dans save_payments: {e}")
        try:
            app = App.get_running_app()
            root = app.root
            if hasattr(root, "refresh_history"):
                root.refresh_history()
        except Exception as e:
            logger.error(f"Erreur refresh: {e}")

    def update_totals(self):
        try:
            db = get_database()

            if self.current_payment_date:
                daily = db.get_revenue_for_date(self.current_payment_date)
            else:
                daily = 0

            weekly = db.get_weekly_revenue()

            if hasattr(self, "ids"):
                if hasattr(self.ids, "daily_label"):
                    self.ids.daily_label.text = f"Jour: {daily:.2f} AR"
                if hasattr(self.ids, "weekly_label"):
                    self.ids.weekly_label.text = f"Semaine: {weekly:.2f} AR"

            marked_count = len(self.pending_payments)
            total_due = 0

            if hasattr(self, "ids") and hasattr(self.ids, "daily_payments_list"):
                for widget in self.ids.daily_payments_list.children:
                    if hasattr(widget, "montant_journalier_value"):
                        total_due += widget.montant_journalier_value

            if hasattr(self, "ids") and hasattr(self.ids, "current_date_label"):
                self.ids.current_date_label.text = (
                    f"Paiements du {self.current_payment_date or ''} - "
                    f"{marked_count} sélectionnés - Total: {total_due:.2f} AR"
                )
        except Exception as e:
            logger.error(f"Erreur dans update_totals: {e}")

    def add_manual_payment(self):
        loan_id_text = self.ids.manual_loan_input.text.strip()
        montant_text = self.ids.manual_amount_input.text.strip()
        date_text = self.ids.manual_date_input.text.strip()

        if not loan_id_text or not montant_text:
            logger.warning("Veuillez entrer le numéro de prêt et le montant")
            return

        try:
            loan_id = int(loan_id_text)
            montant = float(montant_text)
        except ValueError:
            logger.warning("Format invalide")
            return

        if montant <= 0:
            logger.warning("Montant invalide")
            return

        payment_date = None
        if date_text:
            try:
                day, month, year = date_text.split("/")
                payment_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00"
            except:
                logger.warning("Format date invalide, utilisation de la date actuelle")

        db = get_database()
        try:
            db.record_payment(loan_id, montant, date_paiement=payment_date)
            logger.info(
                f"Paiement manuel enregistré: prêt {loan_id}, montant {montant}"
            )
            self.ids.manual_loan_input.text = ""
            self.ids.manual_amount_input.text = ""
            self.ids.manual_date_input.text = self.get_current_date()
            self.refresh_daily_payments()
            self.update_totals()
        except Exception as e:
            logger.error(f"Erreur: {e}")


class HistoryScreen(MDScreen):
    def on_enter(self):
        self.refresh_transactions()
        self.update_totals()

    def refresh_transactions(self):
        db = get_database()
        transactions = db.get_all_transactions()
        logger.info(f"refresh_transactions: found {len(transactions)} transactions")
        self.ids.transactions_list.clear_widgets()
        for t in transactions:
            date_str = t["date_paiement"].replace("T", " ").split(".")[0]
            item = TransactionListItem(
                client_nom=t["client_nom"],
                lampe_numero=t["lampe_numero"],
                date_paiement=date_str,
                montant=f"{t['montant']:.2f}",
            )
            item.transaction_id = t["id"]
            self.ids.transactions_list.add_widget(item)
        self.update_totals()

    def update_totals(self):
        from datetime import date

        db = get_database()
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()
        monthly = db.get_monthly_revenue()
        self.ids.daily_label.text = f"Aujourd'hui: {daily:.2f} AR"
        self.ids.weekly_label.text = f"Semaine: {weekly:.2f} AR"
        self.ids.monthly_label.text = f"Mois: {monthly:.2f} AR"
        self.ids.current_date_label.text = (
            f"Historique - {date.today().strftime('%d/%m/%Y')}"
        )

    def filter_transactions(self):
        date_text = self.ids.history_date_input.text.strip()
        if not date_text:
            self.refresh_transactions()
            return
        try:
            day, month, year = date_text.split("/")
            filter_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            logger.warning("Format date invalide")
            return
        db = get_database()
        transactions = db.get_all_transactions()
        filtered = [
            t for t in transactions if t["date_paiement"].startswith(filter_date)
        ]
        self.ids.transactions_list.clear_widgets()
        for t in filtered:
            date_str = t["date_paiement"].replace("T", " ").split(".")[0]
            item = TransactionListItem(
                client_nom=t["client_nom"],
                lampe_numero=t["lampe_numero"],
                date_paiement=date_str,
                montant=f"{t['montant']:.2f}",
            )
            item.transaction_id = t["id"]
            self.ids.transactions_list.add_widget(item)

    def filter_today_transactions(self):
        from datetime import date

        today = date.today().isoformat()
        db = get_database()
        transactions = db.get_all_transactions()
        filtered = [t for t in transactions if t["date_paiement"].startswith(today)]
        self.ids.transactions_list.clear_widgets()
        for t in filtered:
            item = TransactionListItem(
                client_nom=t["client_nom"],
                lampe_numero=t["lampe_numero"],
                date_paiement=t["date_paiement"].replace("T", " ").split(".")[0],
                montant=f"{t['montant']:.2f}",
            )
            item.transaction_id = t["id"]
            self.ids.transactions_list.add_widget(item)

    def filter_this_month_transactions(self):
        from datetime import date

        today = date.today()
        month_start = today.replace(day=1).isoformat()
        db = get_database()
        transactions = db.get_all_transactions()
        filtered = [
            t
            for t in transactions
            if month_start <= t["date_paiement"].split("T")[0] <= today.isoformat()
        ]
        self.ids.transactions_list.clear_widgets()
        for t in filtered:
            item = TransactionListItem(
                client_nom=t["client_nom"],
                lampe_numero=t["lampe_numero"],
                date_paiement=t["date_paiement"].replace("T", " ").split(".")[0],
                montant=f"{t['montant']:.2f}",
            )
            item.transaction_id = t["id"]
            self.ids.transactions_list.add_widget(item)


class LampManagerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = DatabaseManager()

    def build(self):
        Builder.load_file("style.kv")
        return RootWidget()


if __name__ == "__main__":
    LampManagerApp().run()
