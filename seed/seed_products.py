"""Seeder for Pharmaceutical Products (32 commercial formulations)."""

from sqlalchemy.orm import Session
from app.modules.products.models import Product
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="products")

    products_data = [
        ("MED-AMLO-5", "Amlodipine 5mg", "Cardia Care", "Cardiovascular", 45.0, 32.14, 28.93, "10x10 Tablets"),
        ("MED-TELMI-40", "Telmisartan 40mg", "Cardia Care", "Cardiovascular", 85.0, 60.71, 54.64, "10x10 Tablets"),
        ("MED-ATOR-10", "Atorvastatin 10mg", "Cardia Care", "Cardiovascular", 95.0, 67.86, 61.07, "10x10 Tablets"),
        ("MED-MET-500", "Metformin 500mg SR", "Diabetes Care", "Antidiabetic", 35.0, 25.0, 22.5, "10x10 Tablets"),
        ("MED-GLIM-2", "Glimepiride 2mg", "Diabetes Care", "Antidiabetic", 55.0, 39.29, 35.36, "10x10 Tablets"),
        ("MED-VILDA-50", "Vildagliptin 50mg", "Diabetes Care", "Antidiabetic", 140.0, 100.0, 90.0, "10x10 Tablets"),
        ("MED-DAPA-10", "Dapagliflozin 10mg", "Diabetes Care", "Antidiabetic", 175.0, 125.0, 112.5, "10x10 Tablets"),
        ("MED-PANT-40", "Pantoprazole 40mg", "Gastro Care", "Gastroenterology", 75.0, 53.57, 48.21, "10x10 Tablets"),
        ("MED-RAB-20D", "Rabeprazole 20mg + Domperidone", "Gastro Care", "Gastroenterology", 115.0, 82.14, 73.93, "10x10 Capsules"),
        ("MED-ESOM-40", "Esomeprazole 40mg", "Gastro Care", "Gastroenterology", 105.0, 75.0, 67.5, "10x10 Tablets"),
        ("MED-SUCR-SYP", "Sucralfate + Oxetacaine Oral Susp", "Gastro Care", "Gastroenterology", 160.0, 114.29, 102.86, "200ml Bottle"),
        ("MED-AZI-500", "Azithromycin 500mg", "Anti-Infective", "Antibiotic", 120.0, 85.71, 77.14, "1x3 Tablets"),
        ("MED-CEF-200", "Cefixime 200mg", "Anti-Infective", "Antibiotic", 145.0, 103.57, 93.21, "10x10 Tablets"),
        ("MED-AMX-625", "Amoxicillin 500mg + Clavulanic 125mg", "Anti-Infective", "Antibiotic", 185.0, 132.14, 118.93, "1x10 Tablets"),
        ("MED-LEVO-500", "Levofloxacin 500mg", "Anti-Infective", "Antibiotic", 90.0, 64.29, 57.86, "1x10 Tablets"),
        ("MED-ACE-100", "Aceclofenac 100mg + Paracetamol 325mg", "Pain & Ortho", "Analgesic", 65.0, 46.43, 41.79, "10x10 Tablets"),
        ("MED-THIO-4", "Thiocolchicoside 4mg + Aceclofenac", "Pain & Ortho", "Muscle Relaxant", 195.0, 139.29, 125.36, "10x10 Tablets"),
        ("MED-ETOR-90", "Etoricoxib 90mg", "Pain & Ortho", "Analgesic", 110.0, 78.57, 70.71, "10x10 Tablets"),
        ("MED-MON-10LC", "Montelukast 10mg + Levocetirizine 5mg", "Respiratory", "Antiallergic", 125.0, 89.29, 80.36, "10x10 Tablets"),
        ("MED-ACE-NAC", "Acetylcysteine 600mg Effervescent", "Respiratory", "Mucolytic", 220.0, 157.14, 141.43, "10 Tablets Tube"),
        ("MED-BUD-INH", "Budesonide 200mcg Inhaler", "Respiratory", "Inhaler", 280.0, 200.0, 180.0, "200 Metered Doses"),
        ("MED-CAL-D3", "Calcium 500mg + Vitamin D3", "Nutritional", "Supplements", 90.0, 64.29, 57.86, "1x15 Tablets"),
        ("MED-MVT-GOLD", "Multivitamin & Minerals Softgel", "Nutritional", "Supplements", 165.0, 117.86, 106.07, "10x10 Softgels"),
        ("MED-IRON-SYP", "Ferrous Ascorbate + Folic Acid Syrup", "Nutritional", "Haematinic", 135.0, 96.43, 86.79, "150ml Bottle"),
        ("MED-PRE-GAB", "Pregabalin 75mg + Methylcobalamin", "Neuro Care", "Neuropathic Pain", 180.0, 128.57, 115.71, "10x10 Capsules"),
        ("MED-CIT-500", "Citicoline 500mg", "Neuro Care", "Cerebral Activator", 380.0, 271.43, 244.29, "10x10 Tablets"),
        ("MED-ITRA-200", "Itraconazole 200mg", "Derma Care", "Antifungal", 240.0, 171.43, 154.29, "1x10 Capsules"),
        ("MED-CLO-CRM", "Clobetasol Propionate 0.05% Cream", "Derma Care", "Topical Steroid", 85.0, 60.71, 54.64, "30g Tube"),
        ("MED-FUS-OINT", "Fusidic Acid 2% Ointment", "Derma Care", "Antibacterial", 95.0, 67.86, 61.07, "15g Tube"),
        ("MED-URS-300", "Ursodeoxycholic Acid 300mg", "Hepato Care", "Hepatoprotective", 320.0, 228.57, 205.71, "10x10 Tablets"),
        ("MED-SIL-50", "Sildenafil Citrate 50mg", "Urology Care", "Urology", 150.0, 107.14, 96.43, "1x4 Tablets"),
        ("MED-TAMS-04", "Tamsulosin 0.4mg + Dutasteride 0.5mg", "Urology Care", "Urology", 210.0, 150.0, 135.0, "10x10 Tablets"),
    ]

    for code, name, brand, cat, mrp, ptr, pts, pack in products_data:
        existing = session.query(Product).filter(Product.code == code).first()
        if existing:
            changed = False
            if existing.mrp != mrp:
                existing.mrp = mrp
                changed = True
            if existing.ptr != ptr:
                existing.ptr = ptr
                changed = True
            if existing.pts != pts:
                existing.pts = pts
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            p = Product(
                code=code,
                name=name,
                brand=brand,
                category=cat,
                mrp=mrp,
                ptr=ptr,
                pts=pts,
                packaging=pack,
                is_active=True,
            )
            session.add(p)
            result.created += 1

    session.flush()
    return result
