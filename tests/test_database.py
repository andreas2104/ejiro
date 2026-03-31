import pytest
import os
import tempfile


@pytest.fixture
def test_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def db_manager(test_db):
    from database import DatabaseManager

    db = DatabaseManager(test_db)
    yield db


class TestClientManagement:
    def test_add_client(self, db_manager):
        client_id = db_manager.add_client("Test Client", "0123456789", "Test Address")
        assert client_id > 0
        client = db_manager.get_client_by_id(client_id)
        assert client["nom"] == "Test Client"
        assert client["telephone"] == "0123456789"

    def test_get_all_clients(self, db_manager):
        db_manager.add_client("Client 1", "0123456789", "Address 1")
        db_manager.add_client("Client 2", "0123456788", "Address 2")
        clients = db_manager.get_all_clients()
        assert len(clients) == 2

    def test_update_client(self, db_manager):
        client_id = db_manager.add_client("Original", "0123456789", "Address")
        db_manager.update_client(client_id, "Updated", "0987654321", "New Address")
        client = db_manager.get_client_by_id(client_id)
        assert client["nom"] == "Updated"


class TestLampManagement:
    def test_add_lamp(self, db_manager):
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        assert lamp_id > 0
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["numero"] == "LAMP001"
        assert lamp["etat"] == "disponible"

    def test_get_all_lamps(self, db_manager):
        db_manager.add_lamp_with_etat("LAMP001", "disponible")
        db_manager.add_lamp_with_etat("LAMP002", "louée")
        lamps = db_manager.get_all_lamps()
        assert len(lamps) == 2

    def test_update_lamp(self, db_manager):
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        db_manager.update_lamp(lamp_id, "LAMP001", "louée")
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "louée"

    def test_delete_lamp(self, db_manager):
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        db_manager.delete_lamp(lamp_id)
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp is None


class TestLoanManagement:
    def test_assign_lamp_to_client(self, db_manager):
        client_id = db_manager.add_client("Test Client", "0123456789", "Address")
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 500.0)
        assert loan_id > 0
        loans = db_manager.get_active_loans()
        assert len(loans) == 1
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "louée"

    def test_close_loan(self, db_manager):
        client_id = db_manager.add_client("Test Client", "0123456789", "Address")
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 500.0)
        db_manager.close_loan(loan_id)
        loans = db_manager.get_all_loans()
        assert loans[0]["statut"] == "terminé"
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "disponible"


class TestPayment:
    def test_record_payment(self, db_manager):
        client_id = db_manager.add_client("Test Client", "0123456789", "Address")
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 500.0)
        payment_id = db_manager.record_payment(loan_id, 500.0)
        assert payment_id > 0
        daily = db_manager.get_daily_revenue()
        assert daily == 500.0

    def test_weekly_revenue(self, db_manager):
        client_id = db_manager.add_client("Test Client", "0123456789", "Address")
        lamp_id = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 500.0)
        db_manager.record_payment(loan_id, 500.0)
        db_manager.record_payment(loan_id, 300.0)
        weekly = db_manager.get_weekly_revenue()
        assert weekly == 800.0


class TestPretEndToEnd:
    def test_full_pret_lifecycle(self, db_manager):
        client_id = db_manager.add_client("Jean Dupont", "0770000000", "Parakou")
        assert client_id > 0

        lamp_id = db_manager.add_lamp_with_etat("L001", "disponible")
        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "disponible"

        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 300.0)
        assert loan_id > 0

        loans = db_manager.get_active_loans()
        assert len(loans) == 1
        assert loans[0]["montant_journalier"] == 300.0
        assert loans[0]["client_nom"] == "Jean Dupont"
        assert loans[0]["lamps_numero"] == "L001"

        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "louée"

        payment_id = db_manager.record_payment(loan_id, 300.0)
        assert payment_id > 0

        daily_rev = db_manager.get_daily_revenue()
        assert daily_rev == 300.0

        db_manager.close_loan(loan_id)

        loans = db_manager.get_all_loans()
        assert loans[0]["statut"] == "terminé"

        lamp = db_manager.get_lamp_by_id(lamp_id)
        assert lamp["etat"] == "disponible"

    def test_multiple_loans_same_client(self, db_manager):
        client_id = db_manager.add_client("Alice", "0770000001", "Cotonou")
        lamp1 = db_manager.add_lamp_with_etat("L002", "disponible")
        lamp2 = db_manager.add_lamp_with_etat("L003", "disponible")

        _ = db_manager.assign_lamps_to_client(client_id, lamp1, 400.0)
        _ = db_manager.assign_lamps_to_client(client_id, lamp2, 500.0)

        active = db_manager.get_active_loans()
        assert len(active) == 2

    def test_unpaid_loans_workflow(self, db_manager):
        client_id = db_manager.add_client("Bob", "0770000002", "Porto-Novo")
        lamp_id = db_manager.add_lamp_with_etat("L004", "disponible")
        loan_id = db_manager.assign_lamps_to_client(client_id, lamp_id, 250.0)

        unpaid = db_manager.get_unpaid_loans_today()
        assert len(unpaid) == 1
        assert unpaid[0]["client_nom"] == "Bob"

        db_manager.record_payment(loan_id, 250.0)

        unpaid = db_manager.get_unpaid_loans_today()
        assert len(unpaid) == 0
