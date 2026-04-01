# e-Jiro - Lamp Rental Management App

A Kivy/KivyMD desktop/mobile application for managing solar/rechargeable lamp loans. A provider rents lamps to clients with daily fees for recharging.

## Features

- **Dashboard**: View daily/weekly revenue, client count, lamp count, active loans
- **Client Management**: Add, edit, delete clients with name, phone, address
- **Lamp Inventory**: Manage lamp stock with status (disponible, louée, maintenance)
- **Loan Management**: Assign lamps to clients with daily rental price (montant_journalier)
- **Payment Tracking**: 
  - Track daily payments per client
  - View payment history with filtering (today, this week, this month)
  - Toggle payment status per loan
  - **PDF Export**: Generate payment list reports
- **Settings**: Configure business name, default rate, currency

## Tech Stack

- **Framework**: Kivy with KivyMD
- **Language**: Python 3
- **Database**: SQLite (local)
- **Architecture**: main.py (logic) + style.kv (UI design) + pdf_generator.py

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
lamps: id, numero (unique), etat ('disponible', 'louée', 'maintenance')
prets: id, client_id, lampe_id, date_debut, date_fin, montant_journalier, statut ('actif', 'terminé')
transactions: id, pret_id, date_paiement, montant, type ('journalier')
settings: key, value (business_name, default_rate, currency)
```

## Project Structure (Current - To Refactor)

```
.
├── main.py           # App entry point, ScreenManager, all screens - NEEDS SPLITTING
├── database.py       # DatabaseManager class (CRUD operations)
├── style.kv         # Custom widget styles and screen layouts
├── pdf_generator.py  # PDF report generation
├── tests/
│   └── test_database.py  # Database layer tests
└── venv/            # Virtual environment
```

## Refactoring Plan

See [AGENTS.md](AGENTS.md) for detailed refactoring guidelines including:
- Target folder structure
- Critical rules to avoid crashes
- Import order requirements
- Common error fixes

## Payment Rules

1. Show clients with active loans on selected date (loans where date_debut <= date AND (statut='actif' OR date_fin >= date))
2. Per loan, check if payment exists in transactions table for that date
3. User toggles checkbox to mark as paid/unpaid → creates/deletes transaction record
4. Client shows as "paid" only if ALL their loans for that day are paid

## PDF Export

- Generated from payment screen
- Saved in Downloads folder as `listpaiment_YYYY-MM-DD.pdf`
- Contains: Client name, phone, lamp number, amount

## Currency

Default currency is "Ar" (Ariary - Madagascar). Configurable in Settings.

## License

MIT License