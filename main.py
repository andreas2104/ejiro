from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton


class ClientListItem(BoxLayout):
    client_name = StringProperty()
    client_telephone = StringProperty()
    client_adresse = StringProperty()


from database import DatabaseManager


class DashboardScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.update_revenue())

    def update_revenue(self):
        db = App.get_running_app().database
        daily = db.get_daily_revenue()
        weekly = db.get_weekly_revenue()
        self.ids.daily_label.text = f"Journalier: {daily:.2f} CFA"
        self.ids.weekly_label.text = f"Hebdomadaire: {weekly:.2f} CFA"


class ClientFormModal(Popup):
    nom_input = ObjectProperty()
    telephone_input = ObjectProperty()
    adresse_input = ObjectProperty()
    form_title = ObjectProperty()
    save_button = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clients_screen = None
        self.mode = "add"
        self.selected_client_id = None
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
            print("Nom et téléphone requis")
            return

        db = App.get_running_app().database
        try:
            if self.mode == "edit" and self.selected_client_id:
                db.update_client(self.selected_client_id, nom, telephone, adresse)
                print("Client modifié:", nom)
            else:
                db.add_client(nom, telephone, adresse)
                print("Client ajouté:", nom)
            self.clients_screen.refresh_clients()
            self.dismiss()
        except Exception as e:
            print(f"Erreur: {e}")

    def dismiss(self, *args):
        super().dismiss()


class ClientsScreen(MDScreen):
    selected_client_id = None

    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_clients())
        self.modal = ClientFormModal()

    def show_client_form(self, mode):
        if mode == "edit":
            if not self.selected_client_id:
                print("Aucun client sélectionné")
                return
            db = App.get_running_app().database
            client = db.get_client_by_id(self.selected_client_id)
            self.modal.open(self, "edit", client)
        else:
            self.modal.open(self, "add")

    def refresh_clients(self):
        db = App.get_running_app().database
        clients = db.get_all_clients()
        self.ids.clients_list.data = [
            {
                "client_name": c["nom"],
                "client_telephone": c["telephone"],
                "client_adresse": c["adresse"] or "Pas d'adresse",
                "client_id": c["id"],
                "on_press": lambda c=c: self.select_client(c["id"]),
            }
            for c in clients
        ]
        self.selected_client_id = None

    def select_client(self, client_id):
        self.selected_client_id = client_id

    def delete_client(self):
        if not self.selected_client_id:
            print("Aucun client sélectionné")
            return
        db = App.get_running_app().database
        try:
            db.delete_client(self.selected_client_id)
            print("Client supprimé")
            self.refresh_clients()
        except Exception as e:
            print(f"Erreur: {e}")

    def delete_client(self):
        if not self.selected_client_id:
            print("Aucun client sélectionné")
            return
        db = App.get_running_app().database
        try:
            db.delete_client(self.selected_client_id)
            print("Client supprimé")
            self.refresh_clients()
        except Exception as e:
            print(f"Erreur: {e}")


class InventoryScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.refresh_inventory())

    def refresh_inventory(self):
        db = App.get_running_app().database
        Lampes = db.get_all_lampes()
        self.ids.inventory_list.data = [
            {"text": f"{lamp['numero']} - {lamp['etat']}"} for lamp in Lampes
        ]

    def add_lampe(self, numero: str):
        db = App.get_running_app().database
        try:
            db.add_lampe(numero)
            self.refresh_inventory()
            print("Lampe ajoutée")
        except Exception as e:
            print(f"Erreur: {e}")


class LoanScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_data())

    def load_data(self):
        db = App.get_running_app().database
        clients = db.get_all_clients()
        self.ids.client_spinner.values = [c["nom"] for c in clients]
        available_lamps = [
            lamp for lamp in db.get_all_lampes() if lamp["etat"] == "disponible"
        ]
        self.ids.lampe_spinner.values = [lamp["numero"] for lamp in available_lamps]

    def assign_lampe(self, client_nom: str, lampe_numero: str):
        db = App.get_running_app().database
        clients = db.get_all_clients()
        client = next((c for c in clients if c["nom"] == client_nom), None)
        if not client:
            print("Client non trouvé")
            return

        lampe = next(
            (lamp for lamp in db.get_all_lampes() if lamp["numero"] == lampe_numero),
            None,
        )
        if not lampe:
            print("Lampe non trouvée")
            return

        try:
            db.assign_lampe_to_client(client["id"], lampe["id"])
            print("Prêt créé")
        except Exception as e:
            print(f"Erreur: {e}")


class PaymentScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_loans())

    def load_loans(self):
        db = App.get_running_app().database
        active_loans = db.get_active_loans()
        self.ids.loan_spinner.values = [
            f"{loan['client_nom']} - Lampe {loan['lampe_numero']}"
            for loan in active_loans
        ]

    def record_payment(self, loan_info: str, montant: float):
        if montant <= 0:
            print("Montant invalide")
            return

        db = App.get_running_app().database
        active_loans = db.get_active_loans()
        loan = next(
            (
                loan_item
                for loan_item in active_loans
                if f"{loan_item['client_nom']} - Lampe {loan_item['lampe_numero']}"
                == loan_info
            ),
            None,
        )
        if not loan:
            print("Prêt non trouvé")
            return

        try:
            db.record_payment(loan["id"], montant)
            print("Paiement enregistré")
        except Exception as e:
            print(f"Erreur: {e}")


class LampManagerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.database = DatabaseManager()

    def build(self):
        Builder.load_file("style.kv")
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(ClientsScreen(name="clients"))
        sm.add_widget(InventoryScreen(name="inventory"))
        sm.add_widget(LoanScreen(name="loan"))
        sm.add_widget(PaymentScreen(name="payment"))
        return sm


if __name__ == "__main__":
    LampManagerApp().run()
