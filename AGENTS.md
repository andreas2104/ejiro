# AGENTS.md - LampManager Project Guidelines

## Project Overview

LampManager is a Kivy + SQLite desktop/mobile application for managing solar/rechargeable lamp loans. A provider rents lamps to clients with daily fees for recharging.

## Tech Stack

- **Framework**: Kivy with KivyMD
- **Language**: Python 3
- **Database**: SQLite (local)
- **Architecture**: main.py (logic) + style.kv (design)

---

## Commands

### Running the Application

```bash
python main.py
```

Or with the virtual environment:

```bash
source venv/bin/activate
python main.py
```

### Running Tests

Run all tests:
```bash
python -m pytest
```

Run a single test:
```bash
python -m pytest tests/test_file.py::TestClass::test_method
```

Or with unittest:
```bash
python -m unittest tests.test_module.TestClass.test_method
```

### Linting / Type Checking

```bash
python -m flake8 .
python -m mypy .
```

---

## Code Style Guidelines

### General Principles

- **Clean Code**: Use F-strings for logging, no global variables
- **Performance**: Use context managers (`with sqlite3.connect(...)`) to avoid memory leaks
- **UI**: Use RecycleView for lists (clients, lamps) for mobile fluidity
- **Kivy**: Use .kv language for all declarative widget definitions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `DatabaseManager`, `DashboardScreen` |
| Functions/methods | snake_case | `add_client()`, `get_daily_sum()` |
| Variables | snake_case | `client_id`, `lamp_number` |
| Constants | UPPER_SNAKE | `MAX_LOANS`, `DB_PATH` |
| Files | snake_case | `database.py`, `main.py` |

### Import Organization

```python
# Standard library
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Third-party (Kivy)
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.lang import Builder

# KivyMD
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

# Local imports
from database import DatabaseManager
```

### Type Annotations

Always use type hints for function signatures:

```python
def add_client(self, nom: str, telephone: str, adresse: str) -> int:
    ...
```

### Database (SQLite)

Use context managers for all database operations:

```python
def get_daily_revenue(self) -> float:
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(montant) FROM transactions WHERE date_paiement = ?", (today,))
        result = cursor.fetchone()[0]
        return result if result else 0.0
```

### Kivy Widgets

- Define UI in .kv files, not in Python
- Use ScreenManager for navigation between screens
- Use RecycleView for long lists (clients, lamps)
- Use KivyMD components for modern UI look

### Error Handling

- Use try/except for database operations
- Log errors with appropriate level (`logger.error()`, `logger.warning()`)
- Show user-friendly error messages in UI via MDDialog or Snackbar
- Validate inputs (no negative amounts, existing lamp numbers)

### Database Schema

The application must ensure these tables exist:

```sql
clients: id, nom, telephone (unique), adresse
lampes: id, numero (unique), etat ('disponible', 'louée', 'maintenance')
prets: id, client_id, lampe_id, date_debut, statut ('actif', 'terminé')
transactions: id, pret_id, date_paiement, montant, type ('journalier')
```

### Business Rules

1. A client can have multiple lamps (each lamp identified by its number)
2. A rented lamp cannot be assigned to another client until the loan is closed
3. Payment is linked to the "recharge" action
4. Display real-time revenue on Dashboard
5. Validate forms (prevent negative amounts or non-existent lamp numbers)

---

## File Structure

```
.
├── main.py           # App entry point, ScreenManager setup
├── app.kv            # Root widget definitions (optional)
├── database.py      # DatabaseManager class
├── style.kv         # Custom widget styles
├── screens/
│   ├── dashboard.py
│   ├── clients.py
│   ├── inventory.py
│   ├── loan.py
│   └── payment.py
└── tests/
    └── test_database.py
```

---

## Testing Strategy

- Unit tests for DatabaseManager methods
- Test database operations in isolation
- Mock UI components when testing business logic