"""
main.py — e-Jiro application entry point.

All screens, widgets and popups live under the app/ package:
  app/__init__.py          → EJiroApp (MDApp subclass)
  app/utils.py             → get_database(), DAY_COLORS, helpers
  app/screens/             → one file per screen
  app/widgets/             → one file per widget group
"""
import logging

from app import EJiroApp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    EJiroApp().run()


if __name__ == "__main__":
    main()
