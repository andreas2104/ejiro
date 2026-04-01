from fpdf import FPDF
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class PaymentPDF(FPDF):
    def header(self):
        # Logo
        if os.path.exists("logo_e-jiro.png"):
            try:
                self.image("logo_e-jiro.png", 10, 8, 33)
            except Exception as e:
                logger.error(f"Could not add logo to PDF: {e}")
        
        self.set_font("helvetica", "B", 15)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, "Rapport Journalier de Paiement", 0, 0, "C")
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")

def generate_payment_report(date_str, data, business_name="e-Jiro", output_dir=None):
    """
    Generates a PDF report for payments on a given date.
    data format: list of dicts from DatabaseManager.get_payments_by_date
    """
    try:
        pdf = PaymentPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("helvetica", "", 12)

        # Info Header
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, f"Entreprise: {business_name}", ln=True)
        pdf.cell(0, 10, f"Date du rapport: {date_str}", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 10, f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(10)

        # Split data into paid and unpaid
        paid_entries = []
        unpaid_entries = []

        for client in data:
            for lamp in client["lamps"]:
                entry = {
                    "client": client["client_nom"],
                    "phone": client["client_telephone"],
                    "lamp": lamp["numero"],
                    "amount": lamp["montant"]
                }
                if lamp["is_paid"]:
                    paid_entries.append(entry)
                else:
                    unpaid_entries.append(entry)

        # RECAP
        total_paid = sum(e["amount"] for e in paid_entries)
        total_unpaid = sum(e["amount"] for e in unpaid_entries)

        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Résumé des Paiements", ln=True)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 8, f"Total Collecté: {total_paid:,.0f} Ar", ln=True)
        pdf.cell(0, 8, f"Total Restant: {total_unpaid:,.0f} Ar", ln=True)
        pdf.ln(5)

        # Table Header Function
        def draw_table_header():
            pdf.set_fill_color(200, 220, 255)
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(60, 10, "Client", 1, 0, "C", True)
            pdf.cell(40, 10, "Téléphone", 1, 0, "C", True)
            pdf.cell(35, 10, "Lampe", 1, 0, "C", True)
            pdf.cell(50, 10, "Montant (Ar)", 1, 1, "C", True)
            pdf.set_font("helvetica", "", 10)

        # PAID SECTION
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(0, 100, 0) # Dark Green
        pdf.cell(0, 10, "LISTE DES PAIEMENTS EFFECTUÉS", ln=True)
        pdf.set_text_color(0, 0, 0)
        draw_table_header()
        
        if not paid_entries:
            pdf.cell(0, 10, "Aucun paiement effectué pour cette date.", 1, 1, "C")
        else:
            for entry in paid_entries:
                pdf.cell(60, 10, entry["client"][:30], 1)
                pdf.cell(40, 10, entry["phone"], 1)
                pdf.cell(35, 10, entry["lamp"], 1)
                pdf.cell(50, 10, f"{entry['amount']:,.0f}", 1, 1, "R")
        
        pdf.ln(10)

        # UNPAID SECTION
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(150, 0, 0) # Dark Red
        pdf.cell(0, 10, "LISTE DES PAIEMENTS NON EFFECTUÉS", ln=True)
        pdf.set_text_color(0, 0, 0)
        draw_table_header()

        if not unpaid_entries:
            pdf.cell(0, 10, "Tous les paiements ont été effectués !", 1, 1, "C")
        else:
            for entry in unpaid_entries:
                pdf.cell(60, 10, entry["client"][:30], 1)
                pdf.cell(40, 10, entry["phone"], 1)
                pdf.cell(35, 10, entry["lamp"], 1)
                pdf.cell(50, 10, f"{entry['amount']:,.0f}", 1, 1, "R")

        # Output
        filename = f"listpaiment_{date_str}.pdf"
        if output_dir:
            filename = os.path.join(output_dir, filename)
            
        pdf.output(filename)
        logger.info(f"PDF Report generated: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise
