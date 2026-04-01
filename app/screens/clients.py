"""
app/screens/clients.py — ClientFormModal popup and ClientsScreen.
"""
import logging

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from app.utils import get_database
from app.widgets.list_items import ClientListItem

logger = logging.getLogger(__name__)


class ClientFormModal(Popup):
    """Modal dialog for adding or editing a client."""

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
    """Screen listing all clients with add / edit / delete actions."""
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
