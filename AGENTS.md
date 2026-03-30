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
# Or with venv:
source venv/bin/activate && python main.py
```

### Running Tests

```bash
python -m pytest
python -m pytest tests/test_database.py
python -m pytest tests/test_database.py::TestDatabaseManager::test_add_client
python -m pytest -k "test_add"
python -m pytest -v
```

### Linting / Type Checking

```bash
python -m flake8 . --max-line-length=100
python -m mypy .
```

---

## Code Style Guidelines

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `DatabaseManager`, `DashboardScreen` |
| Functions/methods | snake_case | `add_client()`, `get_daily_sum()` |
| Variables | snake_case | `client_id`, `lamp_number` |
| Constants | UPPER_SNAKE | `MAX_LOANS`, `DB_PATH` |
| Files | snake_case | `database.py`, `main.py` |
| Database tables | singular, lowercase | `clients`, `lampes`, `prets` |

### Import Organization (in this order)

1. Standard library (`sqlite3`, `datetime`, `logging`)
2. Type hints (`typing.Optional`, `typing.List`)
3. Third-party Kivy (`kivy.app`, `kivy.uix.*`)
4. KivyMD (`kivymd.app`, `kivymd.uix.*`)
5. Local imports (`from database import DatabaseManager`)

### Type Annotations

Always use type hints for function signatures and return types:

```python
def add_client(self, nom: str, telephone: str, adresse: str) -> int:
    ...

def get_all_clients(self) -> List[Dict[str, Any]]:
    ...

def get_client_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
    ...
```

### Formatting

- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use blank lines sparingly to separate logical sections

### Database (SQLite)

Use context managers for all database operations. Always use parameterized queries (`?` placeholder) to prevent SQL injection.

```python
def get_daily_revenue(self) -> float:
    today = datetime.now().date().isoformat()
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(montant) FROM transactions WHERE date_paiement LIKE ?",
            (f"{today}%",)
        )
        result = cursor.fetchone()[0]
        return result if result else 0.0
```

### Kivy/KivyMD Widgets

- Define UI in .kv files (style.kv), not in Python
- Use ScreenManager for navigation between screens
- Use RecycleView for long lists (clients, lamps)
- Use Clock.schedule_once for delayed UI updates in on_enter methods

### Error Handling

- Use try/except for database operations, re-raise with logging
- Log errors with appropriate level (`logger.error()`, `logger.warning()`)
- Validate inputs (no negative amounts, existing lamp numbers)
- Raise descriptive exceptions (e.g., `ValueError`, `sqlite3.IntegrityError`)

### Database Schema

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
├── database.py       # DatabaseManager class
├── style.kv         # Custom widget styles
├── screens/
│   ├── dashboard.py
│   ├── clients.py
│   ├── inventory.py
│   ├── loan.py
│   └── payment.py
└── tests/
    └── (add test files here)
```
