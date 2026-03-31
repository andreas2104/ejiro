import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "lampmanager.db"


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    telephone TEXT UNIQUE NOT NULL,
                    adresse TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE NOT NULL,
                    etat TEXT CHECK(etat IN ('disponible', 'louée', 'maintenance'))
                    DEFAULT 'disponible'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    lampe_id INTEGER NOT NULL,
                    date_debut TEXT NOT NULL,
                    montant_journalier REAL NOT NULL,
                    statut TEXT CHECK(statut IN ('actif', 'terminé')) DEFAULT 'actif',
                    FOREIGN KEY (client_id) REFERENCES clients(id),
                    FOREIGN KEY (lampe_id) REFERENCES lamps(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pret_id INTEGER NOT NULL,
                    date_paiement TEXT NOT NULL,
                    montant REAL NOT NULL,
                    type TEXT CHECK(type IN ('journalier')) DEFAULT 'journalier',
                    FOREIGN KEY (pret_id) REFERENCES prets(id)
                )
            """)
            conn.commit()
            logger.info("Database tables initialized")

    def add_client(self, nom: str, telephone: str, adresse: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO clients (nom, telephone, adresse) VALUES (?, ?, ?)",
                    (nom, telephone, adresse),
                )
                conn.commit()
                logger.info(f"Client added: {nom}")
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                logger.error(f"Error adding client: {e}")
                raise

    def get_all_clients(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nom, telephone, adresse FROM clients")
            rows = cursor.fetchall()
            return [
                {"id": r[0], "nom": r[1], "telephone": r[2], "adresse": r[3]}
                for r in rows
            ]

    def get_client_by_id(self, client_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nom, telephone, adresse FROM clients WHERE id = ?",
                (client_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nom": row[1],
                    "telephone": row[2],
                    "adresse": row[3],
                }
            return None

    def update_client(
        self, client_id: int, nom: str, telephone: str, adresse: str
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE clients SET nom = ?, telephone = ?, adresse = ? WHERE id = ?",
                    (nom, telephone, adresse, client_id),
                )
                conn.commit()
                logger.info(f"Client {client_id} updated")
            except sqlite3.IntegrityError as e:
                logger.error(f"Error updating client: {e}")
                raise

    def delete_client(self, client_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM prets WHERE client_id = ? AND statut = 'actif'",
                (client_id,),
            )
            if cursor.fetchone():
                raise ValueError("Cannot delete client with active loans")
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            logger.info(f"Client {client_id} deleted")

    def add_lampe(self, numero: str, etat: str = "disponible") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO lamps (numero, etat) VALUES (?, ?)", (numero, etat)
                )
                conn.commit()
                logger.info(f"Lamp added: {numero}")
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                logger.error(f"Error adding lamp: {e}")
                raise

    def get_all_lamps(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, numero, etat FROM lamps")
            rows = cursor.fetchall()
            return [{"id": r[0], "numero": r[1], "etat": r[2]} for r in rows]

    def get_lampe_by_numero(self, numero: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, numero, etat FROM lamps WHERE numero = ?", (numero,)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "numero": row[1], "etat": row[2]}
            return None

    def get_lamp_by_id(self, lamp_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, numero, etat FROM lamps WHERE id = ?",
                (lamp_id,),
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "numero": row[1], "etat": row[2]}
            return None

    def update_lamp(self, lamp_id: int, numero: str, etat: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE lamps SET numero = ?, etat = ? WHERE id = ?",
                (numero, etat, lamp_id),
            )
            conn.commit()
            logger.info(f"Lamp {lamp_id} updated")

    def add_lamp_with_etat(self, numero: str, etat: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO lamps (numero, etat) VALUES (?, ?)", (numero, etat)
                )
                conn.commit()
                logger.info(f"Lamp added: {numero}")
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                logger.error(f"Error adding lamp: {e}")
                raise

    def delete_lamp(self, lamp_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lamps WHERE id = ?", (lamp_id,))
            conn.commit()
            logger.info(f"Lamp {lamp_id} deleted")

    def assign_lampe_to_client(
        self, client_id: int, lampe_id: int, montant_journalier: float
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT etat FROM lamps WHERE id = ?", (lampe_id,))
            row = cursor.fetchone()
            if not row or row[0] != "disponible":
                raise ValueError(f"Lamp {lampe_id} is not available")

            cursor.execute(
                "INSERT INTO prets (client_id, lampe_id, date_debut, montant_journalier, statut) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    client_id,
                    lampe_id,
                    datetime.now().isoformat(),
                    montant_journalier,
                    "actif",
                ),
            )
            cursor.execute("UPDATE lamps SET etat = 'louée' WHERE id = ?", (lampe_id,))
            conn.commit()
            logger.info(f"Lamp {lampe_id} assigned to client {client_id}")
            return cursor.lastrowid

    def close_loan(self, pret_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE prets SET statut = 'terminé' WHERE id = ?", (pret_id,)
            )
            cursor.execute("SELECT lampe_id FROM prets WHERE id = ?", (pret_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE lamps SET etat = 'disponible' WHERE id = ?", (row[0],)
                )
            conn.commit()
            logger.info(f"Loan {pret_id} closed")

    def delete_loan(self, pret_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lampe_id FROM prets WHERE id = ?", (pret_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE lamps SET etat = 'disponible' WHERE id = ?", (row[0],)
                )
            cursor.execute("DELETE FROM prets WHERE id = ?", (pret_id,))
            conn.commit()
            logger.info(f"Loan {pret_id} deleted")

    def get_all_loans(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, c.nom, l.numero, p.date_debut, p.montant_journalier, p.statut
                FROM prets p
                JOIN clients c ON p.client_id = c.id
                JOIN lamps l ON p.lampe_id = l.id
                ORDER BY p.id DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "client_nom": r[1],
                    "lampe_numero": r[2],
                    "date_debut": r[3],
                    "montant_journalier": r[4],
                    "statut": r[5],
                }
                for r in rows
            ]

    def get_active_loans(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, c.nom, l.numero, p.date_debut, p.montant_journalier
                FROM prets p
                JOIN clients c ON p.client_id = c.id
                JOIN lamps l ON p.lampe_id = l.id
                WHERE p.statut = 'actif'
            """)
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "client_nom": r[1],
                    "lampe_numero": r[2],
                    "date_debut": r[3],
                    "montant_journalier": r[4],
                }
                for r in rows
            ]

    def is_paid_today(self, pret_id: int) -> bool:
        today = datetime.now().date().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM transactions WHERE pret_id = ? AND date_paiement LIKE ?",
                (pret_id, f"{today}%"),
            )
            return cursor.fetchone()[0] > 0

    def is_paid_for_date(self, pret_id: int, date_str: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM transactions WHERE pret_id = ? AND date_paiement LIKE ?",
                (pret_id, f"{date_str}%"),
            )
            return cursor.fetchone()[0] > 0

    def get_revenue_for_date(self, date_str: str) -> float:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(montant) FROM transactions WHERE date_paiement LIKE ?",
                (f"{date_str}%",),
            )
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def record_payment(
        self,
        pret_id: int,
        montant: float,
        type: str = "journalier",
        date_paiement: str = None,
    ) -> int:
        if montant <= 0:
            raise ValueError("Payment amount must be positive")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            payment_date = (
                date_paiement if date_paiement else datetime.now().isoformat()
            )
            cursor.execute(
                "INSERT INTO transactions (pret_id, date_paiement, montant, type) "
                "VALUES (?, ?, ?, ?)",
                (pret_id, payment_date, montant, type),
            )
            conn.commit()
            logger.info(f"Payment recorded: {montant} for loan {pret_id}")
            return cursor.lastrowid

    def get_daily_revenue(self) -> float:
        today = datetime.now().date().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(montant) FROM transactions WHERE date_paiement LIKE ?",
                (f"{today}%",),
            )
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def get_weekly_revenue(self) -> float:
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        today = datetime.now().date().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(montant) FROM transactions "
                "WHERE date_paiement >= ? AND date_paiement <= ?",
                (week_ago, f"{today}T23:59:59"),
            )
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def get_monthly_revenue(self) -> float:
        today = datetime.now().date()
        first_day_of_month = today.replace(day=1).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(montant) FROM transactions "
                "WHERE date_paiement >= ? AND date_paiement <= ?",
                (first_day_of_month, f"{today.isoformat()}T23:59:59"),
            )
            result = cursor.fetchone()[0]
            return result if result else 0.0

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.id, c.nom, l.numero, t.date_paiement, t.montant, t.type
                FROM transactions t
                JOIN prets p ON t.pret_id = p.id
                JOIN clients c ON p.client_id = c.id
                JOIN lamps l ON p.lampe_id = l.id
                ORDER BY t.date_paiement DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "client_nom": r[1],
                    "lampe_numero": r[2],
                    "date_paiement": r[3],
                    "montant": r[4],
                    "type": r[5],
                }
                for r in rows
            ]
