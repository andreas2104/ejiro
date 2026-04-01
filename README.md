# e-Jiro - Lamp Rental Management App

A Kivy/KivyMD desktop/mobile application for managing solar/rechargeable lamp loans. A provider rents lamps to clients with daily fees for recharging.

## Features

- **Dashboard**: View daily/weekly revenue, client count, lamp count, active loans
- **Client Management**: Add, edit, delete clients with name, phone, address
- **Lamp Inventory**: Manage lamp stock with status (disponible, louée, maintenance)
- **Loan Management**: Assign lamps to clients with daily rental price
- **Payment Tracking**: Track daily payments per client, view payment history
- **Settings**: Configure business name, default rate, currency

## Tech Stack

- **Framework**: Kivy with KivyMD
- **Language**: Python 3
- **Database**: SQLite (local)
- **Architecture**: main.py (logic) + style.kv (UI design)

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python main.py

# Or with specific python
./venv/bin/python main.py
```

## Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_database.py

# Run with verbose output
python -m pytest -v
```

## Linting

```bash
# Flake8 linting
python -m flake8 . --max-line-length=100

# Type checking (if configured)
python -m mypy .
```

## Database Schema

```
clients: id, nom, telephone (unique), adresse
lampes: id, numero (unique), etat ('disponible', 'louée', 'maintenance')
prets: id, client_id, lampe_id, date_debut, montant_journalier, statut ('actif', 'terminé')
transactions: id, pret_id, date_paiement, montant, type ('journalier')
```

## Project Structure

```
.
├── main.py           # App entry point, ScreenManager, screens
├── database.py       # DatabaseManager class (CRUD operations)
├── style.kv         # Custom widget styles and screen layouts
├── tests/
│   └── test_database.py  # Database layer tests
└── venv/            # Virtual environment
```

## Business Rules

1. A client can have multiple lamps (each lamp identified by its number)
2. A rented lamp cannot be assigned to another client until the loan is closed
3. Payment is linked to the "recharge" action
4. Display real-time revenue on Dashboard
5. Validate forms (prevent negative amounts or non-existent lamp numbers)

## Currency

Default currency is "Ar" (Ariary - Madagascar). Configurable in Settings.

## License

MIT License