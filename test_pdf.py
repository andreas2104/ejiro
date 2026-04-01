from app.pdf_generator import generate_payment_report
import os

def test_pdf_generation():
    # Sample data mimicking what DatabaseManager.get_payments_by_date returns
    sample_data = [
        {
            "client_id": 1,
            "client_nom": "John Doe",
            "client_telephone": "0340011122",
            "client_adresse": "Lot 123 Antananarivo",
            "lamps": [
                {"pret_id": 10, "numero": "L-001", "montant": 1000, "is_paid": True},
                {"pret_id": 11, "numero": "L-002", "montant": 1000, "is_paid": False}
            ],
            "total_journalier": 2000,
            "is_paid": False
        },
        {
            "client_id": 2,
            "client_nom": "Jane Smith",
            "client_telephone": "0335566677",
            "client_adresse": "Ambohijatovo",
            "lamps": [
                {"pret_id": 12, "numero": "L-005", "montant": 1500, "is_paid": True}
            ],
            "total_journalier": 1500,
            "is_paid": True
        }
    ]
    
    date_str = "2026-04-01"
    try:
        filename = generate_payment_report(date_str, sample_data)
        if os.path.exists(filename):
            print(f"SUCCESS: {filename} created.")
            # We don't delete it yet so we can inspect it if needed
        else:
            print(f"FAILURE: {filename} was not created.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_pdf_generation()
