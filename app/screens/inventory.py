"""
app/screens/inventory.py — LampFormModal popup and InventoryScreen.
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
from app.widgets.list_items import LampListItem

logger = logging.getLogger(__name__)


class LampFormModal(Popup):
    """Modal dialog for adding or editing a lamp."""

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


class InventoryScreen(MDScreen):
    """Screen listing all lamps with add / edit / delete actions."""
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
