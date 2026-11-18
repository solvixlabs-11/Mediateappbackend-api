"""Seeder for Pharmaceutical Products."""

from sqlalchemy.orm import Session
from app.modules.products.models import Product
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="products")

    products_data = [
        ("MED-AMLO-5", "Amlodipine 5mg", "Cardia Care", "Cardiovascular", 45.0, 32.14, 28.93, "10x10 Tablets"),
        ("MED-TELMI-40", "Telmisartan 40mg", "Cardia Care", "Cardiovascular", 85.0, 60.71, 54.64, "10x10 Tablets"),
        ("MED-ATOR-10", "Atorvastatin 10mg", "Cardia Care", "Cardiovascular", 95.0, 67.86, 61.07, "10x10 Tablets"),
        ("MED-MET-500", "Metformin 500mg SR", "Diabetes & Metabolism", "Antidiabetic", 35.0, 25.0, 22.5, "10x10 Tablets"),
        ("MED-GLIM-2", "Glimepiride 2mg", "Diabetes & Metabolism", "Antidiabetic", 55.0, 39.29, 35.36, "10x10 Tablets"),
        ("MED-PANT-40", "Pantoprazole 40mg", "General Medicine", "Gastroenterology", 75.0, 53.57, 48.21, "10x10 Tablets"),
        ("MED-RAB-20D", "Rabeprazole 20mg + Domperidone", "General Medicine", "Gastroenterology", 115.0, 82.14, 73.93, "10x10 Capsules"),
        ("MED-AZI-500", "Azithromycin 500mg", "General Medicine", "Antibiotic", 120.0, 85.71, 77.14, "1x3 Tablets"),
        ("MED-CEF-200", "Cefixime 200mg", "General Medicine", "Antibiotic", 145.0, 103.57, 93.21, "10x10 Tablets"),
        ("MED-CAL-D3", "Calcium 500mg + Vitamin D3", "General Medicine", "Nutritional", 90.0, 64.29, 57.86, "1x15 Tablets"),
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
