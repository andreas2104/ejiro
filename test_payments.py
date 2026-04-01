import sqlite3
from database import DatabaseManager
from datetime import datetime, timedelta

def test_payment_logic():
    db = DatabaseManager("test_payment.db")
    
    # Setup test data
    client_id = db.add_client("Test User", "123456789", "Test St")
    lamp_id = db.add_lamps("L-TEST-1", "disponible")
    
    # Create loan
    loan_id = db.assign_lamps_to_client(client_id, lamp_id, 1000.0)
    
    today = datetime.now().date().isoformat()
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    
    # 1. Check payments for today (initially unpaid)
    payments_today = db.get_payments_by_date(today)
    assert len(payments_today) == 1
    assert payments_today[0]["is_paid"] == False
    
    # 2. Toggle payment for today
    db.toggle_payment(loan_id, today, 1000.0, True)
    payments_today = db.get_payments_by_date(today)
    assert payments_today[0]["is_paid"] == True
    
    # 3. Check for yesterday (loan was active)
    # Note: date_debut was just set to 'now', so depending on timing it might not be <= yesterday
    # Let's manually backdate the loan for testing history
    with sqlite3.connect("test_payment.db") as conn:
        conn.execute("UPDATE prets SET date_debut = ?", (yesterday + "T00:00:00",))
    
    payments_yesterday = db.get_payments_by_date(yesterday)
    assert len(payments_yesterday) == 1
    assert payments_yesterday[0]["is_paid"] == False
    
    # 4. Toggle payment for yesterday
    db.toggle_payment(loan_id, yesterday, 1000.0, True)
    payments_yesterday = db.get_payments_by_date(yesterday)
    assert payments_yesterday[0]["is_paid"] == True
    
    # 5. Close loan and check tomorrow
    db.close_loan(loan_id)
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    payments_tomorrow = db.get_payments_by_date(tomorrow)
    # Since date_fin is set to now, it won't be >= tomorrow
    assert len(payments_tomorrow) == 0
    
    print("All database payment tests passed!")

if __name__ == "__main__":
    import os
    if os.path.exists("test_payment.db"):
        os.remove("test_payment.db")
    test_payment_logic()
