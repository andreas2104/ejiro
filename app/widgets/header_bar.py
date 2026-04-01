"""
app/widgets/header_bar.py — HeaderBar and RootWidget (navigation drawer + screen host).
"""
import logging

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

logger = logging.getLogger(__name__)


class HeaderBar(BoxLayout):
    """Thin top bar with menu-icon and logo."""
    pass


class RootWidget(BoxLayout):
    """Root layout: navigation drawer + MDScreenManager."""

    def reload_app(self):
        app = App.get_running_app()
        app.database = app.database.__class__()
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
