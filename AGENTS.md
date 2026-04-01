# AGENTS.md - e-Jiro Refactoring Guidelines

This document provides guidelines for refactoring e-Jiro app to separate components and prevent crashes.

---

## Project Overview

e-jiro is a Kivy + SQLite desktop/mobile application for managing solar/rechargeable lamp loans. A provider rents lamps to clients with daily fees for recharging.

## Tech Stack

- **Framework**: Kivy with KivyMD
- **Language**: Python 3
- **Database**: SQLite (local)
- **Architecture**: main.py (logic) + style.kv (UI design) + pdf_generator.py

---

## Current Architecture Problem

The app has ALL code in `main.py` (~1100+ lines) including:
- All screen classes (Dashboard, Clients, Inventory, Loan, Payment, History, Settings)
- All custom widget classes (StatCard, LoanListItem, ClientPaymentItem, etc.)
- All popup classes (ClientFormModal, LampFormModal)
- Event handlers and UI logic

This makes the app hard to maintain and prone to crashes during changes.

---

## Refactoring Target Structure

```
.
├── main.py                    # App entry point only (~50 lines)
├── app/
│   ├── __init__.py           # App class definition
│   ├── database.py           # DatabaseManager (keep existing)
│   ├── pdf_generator.py      # PDF generation (keep existing)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── dashboard.py      # DashboardScreen
│   │   ├── clients.py        # ClientsScreen
│   │   ├── inventory.py      # InventoryScreen
│   │   ├── loan.py           # LoanScreen
│   │   ├── payment.py        # PaymentScreen
│   │   ├── history.py        # HistoryScreen
│   │   └── settings.py       # SettingsScreen
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── stat_card.py      # StatCard
│   │   ├── loan_list_item.py # LoanListItem
│   │   ├── client_payment_item.py
│   │   └── transaction_list_item.py
│   └── popups/
│       ├── __init__.py
│       ├── client_form.py    # ClientFormModal
│       └── lamp_form.py      # LampFormModal
├── style.kv                  # Keep in root (Kivy requirement)
├── tests/
│   └── test_database.py
└── venv/
```

---

## Critical Rules to Avoid Crashes

### 1. Kivy Import Order (MUST FOLLOW)

Always use this import order in EVERY file:

```python
# 1. Standard library
import logging
from datetime import datetime

# 2. Type hints
from typing import Optional, List, Dict, Any

# 3. Kivy core
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.metrics import sp
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior

# 4. KivyMD
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDDatePicker

# 5. Local imports
from database import DatabaseManager
```

### 2. Class Resolution Order (MRO) Fix

When combining KivyMD and ButtonBehavior, always put KivyMD first:

```python
# CORRECT - KivyMD first
class StatCard(MDCard, ButtonBehavior):
    pass

# WRONG - causes MRO error
class StatCard(ButtonBehavior, MDCard):
    pass
```

### 3. KV Language Size Values

Never use quoted "dp" in canvas instructions. Use numbers:

```python
# CORRECT
size: 6, self.height

# WRONG - causes TypeError
size: "6dp", self.height
```

### 4. Property Declaration

Always declare all properties at class level:

```python
# CORRECT
class LoanListItem(BoxLayout):
    client_nom = StringProperty()
    lampe_numero = StringProperty()
    loan_id = NumericProperty()

# WRONG - missing properties cause KeyError
class LoanListItem(BoxLayout):
    client_nom = StringProperty()
    # missing lampe_numero!
```

### 5. Screen Class Registration

When splitting screens, register them in main.py:

```python
# main.py should have:
from app.screens import DashboardScreen, ClientsScreen

# MUST register each screen
sm.add_widget(DashboardScreen(name="dashboard"))
sm.add_widget(ClientsScreen(name="clients"))
```

### 6. Database Manager Import

When importing DatabaseManager, use consistent path:

```python
# From any screen file:
from database import get_database

# NOT: from app.database import get_database
# NOT: import database
```

### 7. Widget Class Naming for KV

When defining a widget in Python that will be used in KV:

```python
# Python
class LoanListItem(BoxLayout):
    client_nom = StringProperty()
    ...

# KV - use exact class name
<LoanListItem>:
    MDLabel:
        text: root.client_nom
```

### 8. Clock.schedule_once Usage

Always use lambda to avoid immediate execution:

```python
# CORRECT
Clock.schedule_once(lambda dt: self.refresh_data())

# WRONG - executes immediately
Clock.schedule_once(self.refresh_data())
```

### 9. Property Type Matching

Match KV property names to Python properties exactly:

```python
# Python
class PaymentItem:
    client_nom = StringProperty()
    total_journalier = StringProperty()
    is_paid = BooleanProperty()

# KV must use exact names
MDLabel:
    text: root.client_nom  # CORRECT
    # text: root.clientName  # WRONG - KeyError!
```

### 10. String Formatting in KV

Don't use function calls directly in KV for complex formatting:

```python
# Python - prepare data
item = PaymentItem(
    total_journalier=f"{client['total_journalier']:.0f}"
)

# KV - just display
MDLabel:
    text: root.total_journalier + " Ar"
```

---

## Database Functions to Keep

Keep these methods in database.py - do NOT move to screens:

- `get_all_clients()`, `add_client()`, `update_client()`, `delete_client()`
- `get_all_lamps()`, `add_lamp()`, `update_lamp()`, `delete_lamp()`
- `get_all_loans()`, `assign_lamps_to_client()`, `close_loan()`, `delete_loan()`
- `record_payment()`, `get_daily_revenue()`, `get_weekly_revenue()`, `get_monthly_revenue()`
- `get_payments_by_date()`, `toggle_payment()`
- `get_all_transactions()`
- `get_clients_count()`, `get_lamps_count()`, `get_active_loans_count()`

---

## Common Crash Patterns to Avoid

| Error | Cause | Fix |
|-------|-------|-----|
| `TypeError: must be real number, not str` | `"6dp"` in canvas size | Use `6` |
| `KeyError: 'lamps_numero'` | Missing property in widget | Add property to class |
| `MRO Error` | Wrong class inheritance order | Put KivyMD first |
| `AttributeError: 'NoneType'` | Missing widget id | Check `self.ids` exists |
| `NameError` | Import not found | Check import paths |

---

## Commands

### Running the Application

```bash
python main.py
# Or with venv:
source venv/bin/activate && python main.py
# Or direct:
./venv/bin/python main.py
```

### Running Tests

```bash
python -m pytest
python -m pytest tests/test_database.py
python -m pytest -v
```

### Linting

```bash
python -m flake8 . --max-line-length=100
```

---

## Testing After Refactoring

After moving each screen/component, run:

```bash
# Quick test - app starts
python main.py

# Full test - database still works
python -m pytest tests/test_database.py -v

# Lint check
python -m flake8 . --max-line-length=100
```

---

## File Structure (Target)

```
.
├── main.py           # App entry point (~50 lines)
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── pdf_generator.py
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── clients.py
│   │   ├── inventory.py
│   │   ├── loan.py
│   │   ├── payment.py
│   │   ├── history.py
│   │   └── settings.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   └── ...
│   └── popups/
│       ├── __init__.py
│       └── ...
├── style.kv
├── tests/
│   └── test_database.py
└── venv/
```

---

## Metadata

- **Last Updated**: 2026-04-01
- **App Version**: 1.0.0
- **Python**: 3.10+
- **Kivy**: 2.3.x
- **KivyMD**: 1.2.x