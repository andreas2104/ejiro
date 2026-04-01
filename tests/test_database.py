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
    from app.database import DatabaseManager

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

    def test_client_with_multiple_lamps_payment_workflow(self, db_manager):
        client_id = db_manager.add_client("Rasoa", "0321234567", "Antananarivo")
        lamp1 = db_manager.add_lamp_with_etat("A001", "disponible")
        lamp2 = db_manager.add_lamp_with_etat("A002", "disponible")
        lamp3 = db_manager.add_lamp_with_etat("A003", "disponible")

        loan1 = db_manager.assign_lamps_to_client(client_id, lamp1, 1000.0)
        loan2 = db_manager.assign_lamps_to_client(client_id, lamp2, 1500.0)
        loan3 = db_manager.assign_lamps_to_client(client_id, lamp3, 2000.0)

        clients = db_manager.get_unpaid_clients_today()
        assert len(clients) == 1
        assert clients[0]["client_nom"] == "Rasoa"
        assert len(clients[0]["lamps"]) == 3
        assert clients[0]["total_journalier"] == 4500.0

        lamp1_info = next(l for l in clients[0]["lamps"] if l["numero"] == "A001")
        assert lamp1_info["montant"] == 1000.0

        db_manager.record_payment(loan1, 1000.0)
        db_manager.record_payment(loan2, 1500.0)
        db_manager.record_payment(loan3, 2000.0)

        clients_after = db_manager.get_unpaid_clients_today()
        assert len(clients_after) == 0

        daily_rev = db_manager.get_daily_revenue()
        assert daily_rev == 4500.0

    def test_pret_list_shows_client_details_on_click(self, db_manager):
        client1 = db_manager.add_client("Rasoa", "0321111111", "Tana")
        client2 = db_manager.add_client("Jean", "0322222222", "Cotonou")

        lamp1 = db_manager.add_lamp_with_etat("B001", "disponible")
        lamp2 = db_manager.add_lamp_with_etat("B002", "disponible")
        lamp3 = db_manager.add_lamp_with_etat("B003", "disponible")

        loan1 = db_manager.assign_lamps_to_client(client1, lamp1, 800.0)
        loan2 = db_manager.assign_lamps_to_client(client2, lamp2, 600.0)
        _ = db_manager.assign_lamps_to_client(client1, lamp3, 1200.0)

        all_loans = db_manager.get_all_loans()
        assert len(all_loans) == 3

        loans_rasoa = [l for l in all_loans if l["client_nom"] == "Rasoa"]
        assert len(loans_rasoa) == 2
        assert sum(l["montant_journalier"] for l in loans_rasoa) == 2000.0

        loans_jean = [l for l in all_loans if l["client_nom"] == "Jean"]
        assert len(loans_jean) == 1
        assert loans_jean[0]["lamps_numero"] == "B002"

    def test_lamp_state_transitions_in_pret(self, db_manager):
        client_id = db_manager.add_client("Test", "0330000000", "TestCity")

        lamp1 = db_manager.add_lamp_with_etat("LAMP001", "disponible")
        lamp2 = db_manager.add_lamp_with_etat("LAMP002", "disponible")

        all_lamps = db_manager.get_all_lamps()
        assert len(all_lamps) == 2

        disponibles = [l for l in all_lamps if l["etat"] == "disponible"]
        assert len(disponibles) == 2

        loan1 = db_manager.assign_lamps_to_client(client_id, lamp1, 500.0)
        lamp1_after = db_manager.get_lamp_by_id(lamp1)
        assert lamp1_after["etat"] == "louée"

        disponibles_after = [
            l for l in db_manager.get_all_lamps() if l["etat"] == "disponible"
        ]
        assert len(disponibles_after) == 1

        loan2 = db_manager.assign_lamps_to_client(client_id, lamp2, 700.0)
        lamp2_after = db_manager.get_lamp_by_id(lamp2)
        assert lamp2_after["etat"] == "louée"

        db_manager.close_loan(loan1)
        lamp1_closed = db_manager.get_lamp_by_id(lamp1)
        assert lamp1_closed["etat"] == "disponible"

        db_manager.close_loan(loan2)
        lamp2_closed = db_manager.get_lamp_by_id(lamp2)
        assert lamp2_closed["etat"] == "disponible"

        all_disponibles = [
            l for l in db_manager.get_all_lamps() if l["etat"] == "disponible"
        ]
        assert len(all_disponibles) == 2
