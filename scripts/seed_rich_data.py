"""Comprehensive Mock Data Seeder for Mediate MR App.

Seeds 50+ of each primary entity:
- 50 Doctors (with full credentials, clinics, geocodes, specializations)
- 50 Chemists (with pharmacies, DL numbers, contact persons)
- 50 Hospitals (with bed counts, types, departments)
- 50 Stockists (with credit days, agencies, contacts)
- Hospital-Doctor mappings
- 10 Territories across metro hubs
- 12 Additional Field MRs & Team members
- 50 Planned Visits (across past, today, and future dates)
- 50 DCR Logged Calls (with POB amounts, talk points, geofence status)
- 50 Post-call analyses and sample/gift product details
- 50 Follow-ups (pending & completed)
- 50 Expenses (DA, TA, Lodging, Misc across SUBMITTED, APPROVED, REJECTED)
- 50 Leave Requests (Casual, Sick, Earned)
- 50 Approval Requests in Manager/Admin Inboxes
- 10 Tour Programs (Draft, Submitted, Approved)
"""

import logging
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.attendance.models import Attendance
from app.modules.approvals.models import ApprovalHistory, ApprovalRequest
from app.modules.customers.models import Chemist, Doctor, Hospital, HospitalDoctor, Stockist
from app.modules.dcr.models import DcrPostCallAnalysis, DcrProductDetail, DcrVisit, FollowUp, PlannedVisit
from app.modules.expenses.models import Expense
from app.modules.leaves.models import LeaveBalance, LeaveRequest
from app.modules.masters.models import Area, City, MasterItem, State
from app.modules.masters.seed import seed_masters
from app.modules.notifications.models import DeviceToken, Notification
from app.modules.orders.models import Order, OrderItem
from app.modules.products.models import Product, ProductVisualAid
from app.modules.tasks.models import Task, TaskComment
from app.modules.territories.models import Territory, UserTerritoryAssignment
from app.modules.tours.models import TourProgram
from app.modules.users.models import ManagerMRAssignment, Role, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FIRST_NAMES = [
    "Rajesh", "Priya", "Vikram", "Ananya", "Suresh", "Meera", "Amit", "Sunita",
    "Rohan", "Pooja", "Arvind", "Sneha", "Rahul", "Kavita", "Manoj", "Divya",
    "Rakesh", "Shweta", "Alok", "Neha", "Deepak", "Swati", "Sanjay", "Tanvi",
    "Vivek", "Ritu", "Gaurav", "Simran", "Nitin", "Aarti", "Ashish", "Pallavi",
    "Harish", "Preeti", "Kunal", "Rachna", "Sachin", "Bhavna", "Pradeep", "Juhi",
    "Vijay", "Archana", "Kiran", "Shilpa", "Sameer", "Aditi", "Manish", "Geeta",
    "Anil", "Meenakshi",
]

LAST_NAMES = [
    "Sharma", "Deshmukh", "Malhotra", "Iyer", "Joshi", "Nambiar", "Patel", "Kulkarni",
    "Mehta", "Verma", "Swamy", "Reddy", "Bajaj", "Nair", "Tiwari", "Chawla",
    "Gupta", "Singh", "Nath", "Agarwal", "Bose", "Menon", "Chopra", "Kapur",
    "Saxena", "Bhatia", "Rao", "Pillai", "Pandey", "Mishra", "Dubey", "Shukla",
    "Bhatnagar", "Sen", "Chatterjee", "Mukherjee", "Das", "Roy", "Banerjee", "Dutta",
    "Ghosh", "Som", "Choudhury", "Bhattacharya", "Saha", "Mitra", "Sengupta", "Pal",
    "Biswas", "Sarkar",
]

SPECIALIZATIONS = [
    "Cardiology", "Pediatrics", "Dermatology", "General Medicine",
    "Orthopedics", "Gynecology & Obstetrics", "Neurology", "ENT",
    "Diabetology & Endocrinology", "Pulmonology", "Gastroenterology", "Ophthalmology",
]

QUALIFICATIONS = [
    "MBBS, MD (Medicine)", "MBBS, MS (Ortho)", "MBBS, MD (Cardiology)",
    "MBBS, DNB (Pediatrics)", "MBBS, DDVL (Derma)", "MBBS, MS (ENT)",
    "MBBS, MD (Diabetology)", "MBBS, DGO (Gynec)", "MBBS, DM (Neurology)",
    "MBBS, MD (Chest)", "MBBS, MS, MCh (Surg)", "MBBS, FCPS (Internal Med)",
]

HOSPITAL_NAMES = [
    ("Lilavati Hospital & Research Centre", "Multi-Specialty", 320),
    ("Breach Candy Hospital Trust", "Super Specialty", 210),
    ("Hinduja Healthcare Surgical", "Super Specialty", 180),
    ("Kokilaben Dhirubhai Ambani Hospital", "Multi-Specialty", 750),
    ("Fortis Hospital Mulund", "Multi-Specialty", 350),
    ("Apollo Hospitals Navi Mumbai", "Super Specialty", 500),
    ("Nanavati Max Super Specialty Hospital", "Multi-Specialty", 350),
    ("Saifee Hospital Charni Road", "Multi-Specialty", 250),
    ("Jaslok Hospital & Research Centre", "Super Specialty", 360),
    ("Sir H. N. Reliance Foundation Hospital", "Multi-Specialty", 345),
    ("Bombay Hospital & Medical Research Centre", "Multi-Specialty", 725),
    ("Holy Family Hospital Bandra", "Multi-Specialty", 260),
    ("KEM Hospital Parel", "General / Govt", 1800),
    ("Ruby Hall Clinic Pune", "Multi-Specialty", 550),
    ("Jehangir Hospital Pune", "Multi-Specialty", 350),
    ("Sahyadri Super Speciality Hospital Deccan", "Super Specialty", 220),
    ("Deenanath Mangeshkar Hospital Pune", "Multi-Specialty", 800),
    ("Max Super Speciality Hospital Saket Delhi", "Super Specialty", 500),
    ("Fortis Escorts Heart Institute Okhla", "Super Specialty", 310),
    ("Indraprastha Apollo Hospital Sarita Vihar", "Multi-Specialty", 710),
    ("Sir Ganga Ram Hospital Rajinder Nagar", "Multi-Specialty", 675),
    ("BLK-Max Super Speciality Hospital Pusa Rd", "Super Specialty", 650),
    ("Manipal Hospital Old Airport Rd Bangalore", "Multi-Specialty", 600),
    ("Aster CMI Hospital Hebbal Bangalore", "Multi-Specialty", 500),
    ("Fortis Hospital Bannerghatta Bangalore", "Super Specialty", 400),
    ("Sakra World Hospital Marathahalli", "Super Specialty", 350),
    ("St. John's Medical College Hospital", "Multi-Specialty", 1350),
    ("Columbia Asia Hospital Whitefield", "Multi-Specialty", 150),
    ("Narayana Health City Bommasandra", "Super Specialty", 1400),
    ("BGS Gleneagles Global Hospital Kengeri", "Multi-Specialty", 450),
    ("Sterling Hospital Ahmedabad", "Multi-Specialty", 300),
    ("Zydus Hospital SG Highway Ahmedabad", "Super Specialty", 550),
    ("Care Hospital Banjara Hills Hyderabad", "Multi-Specialty", 435),
    ("Yashoda Hospital Somajiguda Hyderabad", "Super Specialty", 450),
    ("KIMS Hospitals Secunderabad", "Multi-Specialty", 1000),
    ("Continental Hospitals Gachibowli", "Super Specialty", 750),
    ("MIOT International Manapakkam Chennai", "Super Specialty", 1000),
    ("SIMS Hospital Vadapalani Chennai", "Multi-Specialty", 345),
    ("Apollo Hospitals Greams Road Chennai", "Multi-Specialty", 560),
    ("Amrita Hospital Kochi", "Super Specialty", 1300),
    ("Aster Medcity Cheranalloor Kochi", "Multi-Specialty", 670),
    ("KIMSHEALTH Thiruvananthapuram", "Multi-Specialty", 650),
    ("Peerless Hospitex Hospital Kolkata", "Multi-Specialty", 400),
    ("AMRI Hospital Dhakuria Kolkata", "Super Specialty", 300),
    ("Medica Superspecialty Hospital Mukundapur", "Super Specialty", 500),
    ("Woodlands Multispeciality Hospital Alipore", "Multi-Specialty", 240),
    ("Tata Medical Center Rajarhat Kolkata", "Super Specialty", 437),
    ("Shalby Multi-Specialty Hospital Jaipur", "Multi-Specialty", 237),
    ("Eternal Heart Care Centre Jawahar Circle", "Super Specialty", 220),
    ("Fortis Escorts Hospital Malviya Nagar", "Multi-Specialty", 245),
]

CHEMIST_PREFIXES = [
    "Apollo Pharmacy", "MedPlus Chemist", "Wellness Forever", "Sanjivani Medical",
    "Nobel Chemist", "Religare Wellness", "City Medical Store", "Care & Cure Pharmacy",
    "LifeCare Druggists", "Sai Krupa Medicals", "Shree Ram Pharmacy", "Mahavir Chemist",
    "HealthFirst Pharmacy", "Noble Medicals", "Aarogyam Medico", "Popular Pharmacy",
    "Metro Chemist", "Evergreen Medical Store", "Apex Pharmacy", "Pulse Medicals",
    "Vanguard Chemists", "Universal Medicals", "National Pharmacy", "Suburban Chemists",
    "Trust Chemist & Druggist",
]

STOCKIST_NAMES = [
    "Bharat Pharma Agency", "Shreeji Distributors", "Mahavir Medico Agencies",
    "Metro Drug House", "Prime Health Distributors", "Apex Pharma Agency",
    "Sai Distributors Pharma", "Vardhman Healthcare Agencies", "Galaxy Pharma Link",
    "National Drug Agency", "Kothari Pharma Distributors", "Arihant Medical Agencies",
    "Sun Pharma Traders", "Standard Drug Distributors", "Pioneer Pharma Agency",
    "Omkar Healthcare Distributors", "Vijay Pharma Agencies", "Swastik Drug House",
    "Navkar Medico Traders", "Super Pharma Distributors", "Imperial Healthcare Agency",
    "Kalyan Pharma Link", "Shree Ganesh Distributors", "Surya Pharma Distributors",
    "Unity Drug Agencies", "Royal Healthcare Distributors", "Orient Pharma Agency",
    "Devi Medico Distributors", "Classic Pharma Agencies", "Vibrant Drug Traders",
    "Shanti Pharma Agencies", "Chetan Medical Distributors", "Alok Pharma Link",
    "Krishna Drug House", "Maruti Pharma Distributors", "Riddhi Siddhi Medical Agency",
    "Tirupati Healthcare Distributors", "Balaji Drug Agencies", "Pawan Pharma Traders",
    "Anand Medical Distributors", "Kamal Drug Agency", "Gita Pharma Link",
    "Jalaram Healthcare Traders", "Somani Drug Distributors", "Rajesh Medical Agencies",
    "Ratan Pharma Agency", "New Era Drug Distributors", "Zenith Healthcare Agencies",
    "Kaveri Pharma Link", "Bhawani Medical Distributors",
]

PRODUCTS = [
    ("CardioMet-50", "Cardiovascular & Hypertension"),
    ("Rosuvastatin 20mg", "Lipid Management & Statins"),
    ("GlimiSave-M", "Anti-Diabetic Dual Therapy"),
    ("AzithroMed-500", "Broad-Spectrum Antibiotic"),
    ("Pantop-D", "Gastroprokinetic & PPI"),
    ("TelmiMed-40", "Anti-Hypertensive Angiotensin Blocker"),
    ("CalciRich-D3", "Calcium & Vitamin D3 Softgels"),
    ("Montair-LC", "Anti-Allergic & Bronchodilator"),
    ("NeuroPlus-OD", "Methylcobalamin & Multivitamin"),
    ("DermaSoft Cream", "Topical Anti-Inflammatory"),
]

def seed_rich_data():
    db = SessionLocal()
    try:
        logger.info("Step 1: Checking and seeding core masters...")
        seed_masters(db)
        db.commit()

        # Fetch roles and core users
        mr_role = db.query(Role).filter_by(code="MR").first()
        mgr_role = db.query(Role).filter_by(code="MANAGER").first()

        mr_user = db.query(User).filter_by(email="mr@mediatehealthcare.com").first()
        mgr_user = db.query(User).filter_by(email="manager@mediatehealthcare.com").first()
        admin_user = db.query(User).filter_by(email="admin@mediatehealthcare.com").first()

        if not mr_user or not mgr_user:
            logger.warning("Default dev users not found, skipping user-linked records.")
            return

        # Step 2: Seed Territories
        logger.info("Step 2: Seeding 10 operational Territories...")
        territory_data = [
            ("Mumbai South & Colaba", "TERR-MUM-01", "Mumbai", "South Mumbai key hospitals & clinics"),
            ("Bandra - Andheri West", "TERR-MUM-02", "Mumbai", "Western suburbs Tier 1 clinics"),
            ("Dadar - Parel Hub", "TERR-MUM-03", "Mumbai", "Hospital belt KEM, Tata, Hinduja"),
            ("Thane & Navi Mumbai", "TERR-MUM-04", "Thane", "Apollo, Fortis & suburban clinics"),
            ("Pune Central & Deccan", "TERR-PUN-01", "Pune", "Ruby Hall, Jehangir & Deccan gyms"),
            ("Pune Pimpri - Chinchwad", "TERR-PUN-02", "Pune", "Industrial belt & general hospitals"),
            ("Delhi South & Saket", "TERR-DEL-01", "Delhi", "Max Saket & South Extension"),
            ("Delhi Central & Karol Bagh", "TERR-DEL-02", "Delhi", "Sir Ganga Ram & Central clinics"),
            ("Bangalore Central & MG Road", "TERR-BLR-01", "Bangalore", "Manipal, Bowring & CBD chambers"),
            ("Bangalore East & Whitefield", "TERR-BLR-02", "Bangalore", "Sakra, Columbia Asia & Tech park clinics"),
        ]

        territories = []
        for name, code, hq, desc in territory_data:
            t = db.query(Territory).filter_by(code=code).first()
            if not t:
                t = Territory(name=name, code=code, headquarters=hq, description=desc)
                db.add(t)
                db.flush()
            territories.append(t)
        db.commit()

        # Step 3: Seed 12 Additional Field MRs and Team Members
        logger.info("Step 3: Seeding 12 Team Members (MRs & Area Managers)...")
        team_mrs = [mr_user]
        hashed_pwd = hash_password("Password@123")

        for i in range(1, 13):
            email = f"mr{i}@mediatehealthcare.com"
            existing = db.query(User).filter_by(email=email).first()
            if not existing:
                u = User(
                    email=email,
                    hashed_password=hashed_pwd,
                    full_name=f"{FIRST_NAMES[i]} {LAST_NAMES[i]}",
                    phone=f"+91 98200 {10000 + i}",
                    role_id=mr_role.id,
                )
                db.add(u)
                db.flush()
                # Assign to Manager
                db.add(ManagerMRAssignment(manager_id=mgr_user.id, mr_id=u.id))
                team_mrs.append(u)
            else:
                team_mrs.append(existing)
        db.commit()

        # Step 3b: Assign Users to Territories
        logger.info("Step 3b: Assigning Field Users & Managers to Operational Territories...")
        for t in territories:
            if not db.query(UserTerritoryAssignment).filter_by(user_id=mr_user.id, territory_id=t.id).first():
                db.add(UserTerritoryAssignment(user_id=mr_user.id, territory_id=t.id))
            if not db.query(UserTerritoryAssignment).filter_by(user_id=mgr_user.id, territory_id=t.id).first():
                db.add(UserTerritoryAssignment(user_id=mgr_user.id, territory_id=t.id))

        for idx, u in enumerate(team_mrs):
            t = territories[idx % len(territories)]
            if not db.query(UserTerritoryAssignment).filter_by(user_id=u.id, territory_id=t.id).first():
                db.add(UserTerritoryAssignment(user_id=u.id, territory_id=t.id))
        db.commit()

        # Step 4: Seed 50 Hospitals
        logger.info("Step 4: Seeding 50 Hospitals...")
        hospitals = []
        for i, (h_name, h_type, beds) in enumerate(HOSPITAL_NAMES, start=1):
            code = f"HOSP-{i:03d}"
            h = db.query(Hospital).filter_by(code=code).first()
            if not h:
                t_idx = (i - 1) % len(territories)
                lat = 18.9000 + random.uniform(0.05, 0.35)
                lng = 72.8000 + random.uniform(0.02, 0.15)
                h = Hospital(
                    code=code,
                    name=h_name,
                    type=h_type,
                    contact_person=f"Dr. {FIRST_NAMES[i % len(FIRST_NAMES)]} (MS/Dean)",
                    phone=f"+91 22 260{1000 + i}",
                    email=f"admin@{code.lower()}.org",
                    address=f"Plot {i * 12}, Healthcare Boulevard, Ward-{i}",
                    territory_id=territories[t_idx].id,
                    bed_count=beds,
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    pincode=f"4000{10 + (i % 80):02d}",
                    is_active=True,
                )
                db.add(h)
                db.flush()
            hospitals.append(h)
        db.commit()

        # Step 5: Seed 50 Doctors
        logger.info("Step 5: Seeding 50 Doctors with complete specialty profiles...")
        doctors = []
        categories = ["SUPER_CORE", "CORE", "GENERAL", "POTENTIAL"]
        for i in range(1, 51):
            code = f"DOC-{i:03d}"
            d = db.query(Doctor).filter_by(code=code).first()
            first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
            spec = SPECIALIZATIONS[(i - 1) % len(SPECIALIZATIONS)]
            qual = QUALIFICATIONS[(i - 1) % len(QUALIFICATIONS)]
            cat = categories[(i - 1) % len(categories)]
            t_idx = (i - 1) % len(territories)

            # Geolocation cluster around Mumbai / Pune
            lat = 18.9500 + random.uniform(0.01, 0.28)
            lng = 72.8200 + random.uniform(0.01, 0.12)

            if not d:
                d = Doctor(
                    code=code,
                    full_name=f"Dr. {first} {last}",
                    qualification=qual,
                    specialization=spec,
                    category=cat,
                    phone=f"+91 9820{i:02d} {10000 + i}",
                    email=f"dr.{first.lower()}.{last.lower()}@gmail.com",
                    clinic_name=f"{last} Polyclinic & Care Centre",
                    address=f"Suite {101 + i}, Medical Enclave, Cross Road {i % 15}",
                    territory_id=territories[t_idx].id,
                    pincode=f"4000{20 + (i % 60):02d}",
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    is_active=True,
                )
                db.add(d)
                db.flush()

                # Map to 1-2 Hospitals
                h_target = hospitals[(i - 1) % len(hospitals)]
                db.add(
                    HospitalDoctor(
                        hospital_id=h_target.id,
                        doctor_id=d.id,
                        department=spec,
                        visiting_hours="10:00 AM - 01:00 PM, Mon-Sat",
                        is_primary=True,
                    )
                )
            doctors.append(d)
        db.commit()

        # Step 6: Seed 50 Chemists
        logger.info("Step 6: Seeding 50 Chemists / Pharmacies...")
        chemists = []
        for i in range(1, 51):
            code = f"CHM-{i:03d}"
            c = db.query(Chemist).filter_by(code=code).first()
            prefix = CHEMIST_PREFIXES[(i - 1) % len(CHEMIST_PREFIXES)]
            t_idx = (i - 1) % len(territories)
            lat = 18.9500 + random.uniform(0.01, 0.28)
            lng = 72.8200 + random.uniform(0.01, 0.12)

            if not c:
                c = Chemist(
                    code=code,
                    shop_name=f"{prefix} #{i:02d}",
                    contact_person=f"{FIRST_NAMES[(i + 5) % len(FIRST_NAMES)]} {LAST_NAMES[(i + 5) % len(LAST_NAMES)]}",
                    phone=f"+91 9769{i:02d} {20000 + i}",
                    email=f"orders.chem{i}@gmail.com",
                    dl_number=f"MH-TZ1-20{i:04d}",
                    gstin=f"27AABCU{9000 + i}R1Z5",
                    address=f"Shop {i}, Near Station Road, Sector {i % 12}",
                    territory_id=territories[t_idx].id,
                    pincode=f"4000{15 + (i % 70):02d}",
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    is_active=True,
                )
                db.add(c)
                db.flush()
            chemists.append(c)
        db.commit()

        # Step 7: Seed 50 Stockists
        logger.info("Step 7: Seeding 50 Stockists / Wholesale Distributors...")
        stockists = []
        for i in range(1, 51):
            code = f"STK-{i:03d}"
            s = db.query(Stockist).filter_by(code=code).first()
            s_name = STOCKIST_NAMES[(i - 1) % len(STOCKIST_NAMES)]
            t_idx = (i - 1) % len(territories)
            credit = random.choice([21, 30, 45, 60])

            if not s:
                s = Stockist(
                    code=code,
                    agency_name=f"{s_name} #{i:02d}",
                    contact_person=f"{FIRST_NAMES[(i + 10) % len(FIRST_NAMES)]} {LAST_NAMES[(i + 10) % len(LAST_NAMES)]}",
                    phone=f"+91 9930{i:02d} {30000 + i}",
                    email=f"accounts.stk{i}@pharmaagency.com",
                    dl_number=f"MH-TZ2-30{i:04d}",
                    gstin=f"27AABCS{8000 + i}K1ZX",
                    address=f"Godown {i}, Pharma Transport Complex, Ward {i % 8}",
                    territory_id=territories[t_idx].id,
                    credit_days=credit,
                    pincode=f"4000{30 + (i % 50):02d}",
                    latitude=round(18.9800 + random.uniform(0.01, 0.25), 6),
                    longitude=round(72.8300 + random.uniform(0.01, 0.10), 6),
                    is_active=True,
                )
                db.add(s)
                db.flush()
            stockists.append(s)
        db.commit()

        # Step 8: Seed 50 Planned Visits
        logger.info("Step 8: Seeding 50 Pre-Call Planned Visits...")
        today = date.today()
        plan_statuses = ["PLANNED", "COMPLETED", "PLANNED", "PLANNED", "MISSED"]
        purposes = [
            "Promote CardioMet-50 clinical findings",
            "Collect POB order & stock liquidation check",
            "Introduce Rosuvastatin 20mg new packaging",
            "Follow-up on hospital pharmacy supply",
            "Quarterly review with Chief of Medicine",
            "Deliver product samples and journal reprints",
        ]

        planned_visits = []
        for i in range(1, 51):
            client_uuid = f"plan-seed-{i:03d}"
            existing_pv = db.query(PlannedVisit).filter_by(client_uuid=client_uuid).first()
            if existing_pv:
                planned_visits.append(existing_pv)
                continue

            day_offset = (i % 14) - 5  # past 5 days to next 8 days
            p_date = today + timedelta(days=day_offset)
            target_user = team_mrs[i % len(team_mrs)]
            doc = doctors[(i - 1) % len(doctors)]
            p_status = "COMPLETED" if day_offset < 0 else plan_statuses[i % len(plan_statuses)]

            pv = PlannedVisit(
                user_id=target_user.id,
                plan_date=p_date,
                customer_type="DOCTOR",
                doctor_id=doc.id,
                priority="HIGH" if i % 2 == 0 else "MEDIUM",
                visit_purpose=purposes[i % len(purposes)],
                status=p_status,
                notes=f"Planned discussion on tier {doc.category} potential.",
                client_uuid=client_uuid,
            )
            db.add(pv)
            db.flush()
            planned_visits.append(pv)

        # Step 8b: Seed Today's Planned Visits specifically for mr@mediatehealthcare.com
        logger.info("Step 8b: Seeding Today's Planned Visits for mr@mediatehealthcare.com...")
        today_mr_targets = [
            (doctors[0], "HIGH", "Discuss CardioMet-50 clinical trial findings and patient tolerance", "COMPLETED"),
            (doctors[1], "HIGH", "Quarterly review and deliver product samples with journal reprints", "COMPLETED"),
            (chemists[0], "MEDIUM", "Check inventory stock of CardioMet-50 and Azithro-500", "COMPLETED"),
            (doctors[2], "HIGH", "Introduce Rosuvastatin 20mg new blister pack", "COMPLETED"),
            (chemists[1], "MEDIUM", "Collect chemist POB order for Apollo pharmacy chain", "PLANNED"),
            (doctors[3], "MEDIUM", "Follow-up on hospital pharmacy supply & patient compliance", "PLANNED"),
            (doctors[4], "HIGH", "Detail DermaSoft cream and promote anti-inflammatory benefits", "PLANNED"),
            (stockists[0], "MEDIUM", "Stock liquidation review and monthly settlement verification", "PLANNED"),
        ]
        for idx, (cust, prio, purp, st) in enumerate(today_mr_targets, start=1):
            c_uuid = f"plan-today-mr-{idx:03d}"
            existing_pv = db.query(PlannedVisit).filter_by(client_uuid=c_uuid).first()
            if not existing_pv:
                cust_type = "DOCTOR" if isinstance(cust, Doctor) else ("CHEMIST" if isinstance(cust, Chemist) else "STOCKIST")
                pv = PlannedVisit(
                    user_id=mr_user.id,
                    plan_date=today,
                    customer_type=cust_type,
                    doctor_id=cust.id if cust_type == "DOCTOR" else None,
                    chemist_id=cust.id if cust_type == "CHEMIST" else None,
                    stockist_id=cust.id if cust_type == "STOCKIST" else None,
                    priority=prio,
                    visit_purpose=purp,
                    status=st,
                    notes="Today's high-priority field target",
                    client_uuid=c_uuid,
                )
                db.add(pv)
        db.commit()

        # Step 8c: Ensure Today's Attendance Check-in for mr_user
        logger.info("Step 8c: Ensuring Today's Attendance Check-in for mr@mediatehealthcare.com...")
        today_att = db.query(Attendance).filter_by(user_id=mr_user.id, date=today).first()
        if not today_att:
            db.add(
                Attendance(
                    user_id=mr_user.id,
                    date=today,
                    status="PRESENT",
                    check_in_time=datetime.now().replace(hour=9, minute=15, second=0, microsecond=0),
                    check_in_latitude=19.0520,
                    check_in_longitude=72.8290,
                    check_in_address="Near Lilavati Hospital, Bandra West, Mumbai",
                    check_in_accuracy=12.5,
                    check_in_mock_flag=False,
                    client_uuid=f"att-mr-today-{today.strftime('%Y%m%d')}",
                )
            )
            db.commit()

        # Step 9: Seed 50 DCR Visits (with geofence and call logs)
        logger.info("Step 9: Seeding 50 DCR Logged Calls with talk points...")
        for i in range(1, 51):
            client_uuid = f"dcr-seed-{i:03d}"
            existing_dcr = db.query(DcrVisit).filter_by(client_uuid=client_uuid).first()
            if existing_dcr:
                continue

            day_offset = -1 * (i % 12)  # past 12 days
            v_date = today + timedelta(days=day_offset)
            target_user = team_mrs[i % len(team_mrs)]
            doc = doctors[(i - 1) % len(doctors)]
            pob = round(random.uniform(5000, 85000), 2) if i % 3 == 0 else 0.0

            dcr = DcrVisit(
                user_id=target_user.id,
                dcr_date=v_date,
                customer_type="DOCTOR",
                doctor_id=doc.id,
                call_time=datetime.now() - timedelta(hours=i * 2),
                call_duration_minutes=random.randint(12, 35),
                visit_type="INDEPENDENT",
                latitude=doc.latitude or 19.0760,
                longitude=doc.longitude or 72.8777,
                is_geofence_verified=(i % 10 != 0),  # 90% verified
                distance_to_customer_meters=round(random.uniform(15, 85), 1),
                pob_amount=pob,
                remarks=f"Detailed {PRODUCTS[i % len(PRODUCTS)][0]} and patient tolerance benefits. Doctor expressed positive interest; committed to 5 scripts/week.",
                status="APPROVED" if i <= 20 else "SUBMITTED",
                client_uuid=client_uuid,
            )
            db.add(dcr)
            db.flush()

            # Post-call analysis
            db.add(
                DcrPostCallAnalysis(
                    dcr_visit_id=dcr.id,
                    call_outcome="HIGHLY_INTERESTED" if i % 2 == 0 else "MODERATE",
                    doctor_feedback="Appreciated the scientific monograph and dosage flexibility.",
                    prescription_commitment="HIGH" if i % 3 == 0 else "MEDIUM",
                    next_visit_date=today + timedelta(days=14),
                    follow_up_required=(i % 4 == 0),
                    follow_up_notes="Drop 2 patient starter kits next Monday." if i % 4 == 0 else None,
                )
            )

            # Promoted products lines
            prod1 = PRODUCTS[i % len(PRODUCTS)]
            prod2 = PRODUCTS[(i + 1) % len(PRODUCTS)]
            db.add(
                DcrProductDetail(
                    dcr_visit_id=dcr.id,
                    product_name=prod1[0],
                    sample_quantity=random.randint(2, 6),
                    gift_quantity=random.choice([0, 1]),
                    remarks="Prescriber accepted sample strip.",
                )
            )
            db.add(
                DcrProductDetail(
                    dcr_visit_id=dcr.id,
                    product_name=prod2[0],
                    sample_quantity=random.randint(1, 4),
                    gift_quantity=0,
                    remarks="Literature pamphlet provided.",
                )
            )
        db.commit()

        # Step 9b: Seed Today's Completed DCR Visits specifically for mr@mediatehealthcare.com
        logger.info("Step 9b: Seeding Today's Completed DCR Visits for mr@mediatehealthcare.com...")
        today_dcr_calls = [
            (doctors[0], 25000.0, 10, 15, "Dr. Rajesh Sharma confirmed CardioMet-50 prescribing for 15+ OPD patients. Detailed safety profile."),
            (doctors[1], 18500.0, 11, 45, "Detailed scientific study reprints. Dr. Priya Nair requested 5 more physician sample strips."),
            (chemists[0], 12000.0, 14, 0, "Verified stock movement of CardioMet-50 and Azithro-500. Took reorder POB ₹12,000 for Apollo pharmacy."),
            (doctors[2], 0.0, 15, 30, "Dr. Amit Patel reviewed Rosuvastatin 20mg profile, promised initiation for hyperlipidemia cases next week."),
        ]
        for idx, (cust, pob, hr, mn, rem) in enumerate(today_dcr_calls, start=1):
            c_uuid = f"dcr-today-mr-{idx:03d}"
            existing_dcr = db.query(DcrVisit).filter_by(client_uuid=c_uuid).first()
            if not existing_dcr:
                cust_type = "DOCTOR" if isinstance(cust, Doctor) else "CHEMIST"
                call_dt = datetime.now().replace(hour=hr, minute=mn, second=0, microsecond=0)
                dcr = DcrVisit(
                    user_id=mr_user.id,
                    dcr_date=today,
                    customer_type=cust_type,
                    doctor_id=cust.id if cust_type == "DOCTOR" else None,
                    chemist_id=cust.id if cust_type == "CHEMIST" else None,
                    call_time=call_dt,
                    call_duration_minutes=20,
                    visit_type="INDEPENDENT",
                    latitude=cust.latitude or 19.0520,
                    longitude=cust.longitude or 72.8290,
                    location_accuracy=12.0,
                    distance_to_customer_meters=45.0,
                    is_geofence_verified=True,
                    is_mock_location=False,
                    pob_amount=pob,
                    status="SUBMITTED",
                    remarks=rem,
                    client_uuid=c_uuid,
                )
                db.add(dcr)
                db.flush()

                db.add(
                    DcrPostCallAnalysis(
                        dcr_visit_id=dcr.id,
                        call_outcome="HIGHLY_INTERESTED",
                        doctor_feedback=rem,
                        prescription_commitment="HIGH",
                        next_visit_date=today + timedelta(days=14),
                        follow_up_required=True,
                        follow_up_notes="Deliver commercial packaging sample pack",
                    )
                )
                db.add(
                    DcrProductDetail(
                        dcr_visit_id=dcr.id,
                        product_name="CardioMet-50",
                        sample_quantity=4,
                        gift_quantity=1,
                        remarks="Physician sample given",
                    )
                )
        db.commit()

        # Step 10: Seed 50 Follow-ups
        logger.info("Step 10: Seeding 50 Follow-ups...")
        followup_actions = [
            "Deliver sample pack of CardioMet-50",
            "Collect outstanding POB order from chemist",
            "Provide clinical safety study to Dr. regarding statin interactions",
            "Schedule hospital committee meeting",
            "Check stock movement at primary stockist",
        ]
        for i in range(1, 51):
            due = today + timedelta(days=(i % 10) - 3)
            doc = doctors[(i - 1) % len(doctors)]
            target_user = team_mrs[i % len(team_mrs)]
            client_uuid = f"followup-seed-{i:03d}"
            existing_f = db.query(FollowUp).filter_by(client_uuid=client_uuid).first()
            if existing_f:
                continue

            title = followup_actions[i % len(followup_actions)]
            f = FollowUp(
                user_id=target_user.id,
                customer_type="DOCTOR",
                doctor_id=doc.id,
                due_date=due,
                title=title,
                status="COMPLETED" if (i % 3 == 0) else "PENDING",
                priority="HIGH" if i % 2 == 0 else "MEDIUM",
                notes=f"Reminder priority {(i % 3) + 1}",
                client_uuid=client_uuid,
            )
            db.add(f)

        # Step 10b: Seed MR specific Follow-ups
        for idx in range(1, 6):
            f_uuid = f"followup-mr-{idx:03d}"
            if not db.query(FollowUp).filter_by(client_uuid=f_uuid).first():
                doc = doctors[idx % len(doctors)]
                db.add(
                    FollowUp(
                        user_id=mr_user.id,
                        customer_type="DOCTOR",
                        doctor_id=doc.id,
                        due_date=today + timedelta(days=idx - 1),
                        title=f"Deliver sample pack & follow up on prescribing with Dr. {doc.full_name}",
                        status="PENDING",
                        priority="HIGH" if idx % 2 == 1 else "MEDIUM",
                        notes="Important follow-up task",
                        client_uuid=f_uuid,
                    )
                )
        db.commit()

        # Step 11: Seed 50 Expenses
        logger.info("Step 11: Seeding 50 Expense Claims...")
        exp_types = ["DAILY_ALLOWANCE", "TRAVEL_FARE", "LODGING", "MISCELLANEOUS"]
        exp_statuses = ["SUBMITTED", "APPROVED", "SUBMITTED", "APPROVED", "REJECTED"]
        for i in range(1, 51):
            client_uuid = f"exp-seed-{i:03d}"
            existing_exp = db.query(Expense).filter_by(client_uuid=client_uuid).first()
            if existing_exp:
                continue

            e_date = today - timedelta(days=i)
            target_user = team_mrs[i % len(team_mrs)]
            e_type = exp_types[i % len(exp_types)]
            status = exp_statuses[i % len(exp_statuses)]

            if e_type == "DAILY_ALLOWANCE":
                amount = random.choice([450.0, 550.0, 650.0, 750.0])
                desc = "Field DA as per company headquarters policy"
            elif e_type == "TRAVEL_FARE":
                amount = round(random.uniform(400, 2400), 2)
                desc = f"Inter-city travel fare: Mumbai to Pune Sector {i % 4}"
            elif e_type == "LODGING":
                amount = round(random.uniform(1800, 4200), 2)
                desc = "Hotel overnight stay during tour program"
            else:
                amount = round(random.uniform(200, 850), 2)
                desc = "Printing of scientific reprints & postage"

            exp = Expense(
                user_id=target_user.id,
                expense_date=e_date,
                expense_type=e_type,
                amount=amount,
                description=desc,
                status=status,
                client_uuid=client_uuid,
                rejection_reason="Excess beyond authorized tier limit" if status == "REJECTED" else None,
            )
            db.add(exp)
            db.flush()

            # Create Approval Request for Manager
            appr_status = "PENDING" if status == "SUBMITTED" else status
            appr = ApprovalRequest(
                entity_type="EXPENSE",
                entity_id=exp.id,
                requester_id=target_user.id,
                status=appr_status,
                title=f"Expense Claim - {e_type} (₹{amount:,.0f})",
                details=f"Submitted by {target_user.full_name} for date {e_date}. {desc}",
            )
            db.add(appr)
            db.flush()
            exp.approval_request_id = appr.id

            if appr_status in ("APPROVED", "REJECTED"):
                db.add(
                    ApprovalHistory(
                        request_id=appr.id,
                        approver_id=mgr_user.id,
                        decision=appr_status,
                        comments="Processed per regional budget guidelines.",
                    )
                )
        db.commit()

        # Step 12: Seed 50 Leaves
        logger.info("Step 12: Seeding 50 Leave Requests and Balances...")
        leave_types = ["CASUAL", "SICK", "EARNED"]
        leave_reasons = [
            "Family function and personal emergency",
            "Viral fever and medical rest advised by physician",
            "Annual family vacation",
            "Urgent domestic paperwork and bank work",
            "Child illness and hospital consultation",
        ]
        for u in team_mrs:
            b = db.query(LeaveBalance).filter_by(user_id=u.id, year=today.year).first()
            if not b:
                db.add(
                    LeaveBalance(
                        user_id=u.id,
                        year=today.year,
                        casual_leave_balance=12.0,
                        sick_leave_balance=8.0,
                        earned_leave_balance=15.0,
                    )
                )
        db.commit()

        for i in range(1, 51):
            client_uuid = f"leave-seed-{i:03d}"
            existing_lr = db.query(LeaveRequest).filter_by(client_uuid=client_uuid).first()
            if existing_lr:
                continue

            target_user = team_mrs[i % len(team_mrs)]
            l_type = leave_types[i % len(leave_types)]
            days = random.choice([1.0, 2.0, 3.0, 5.0])
            s_date = today + timedelta(days=(i * 3) - 30)
            e_date = s_date + timedelta(days=int(days) - 1)
            status = exp_statuses[i % len(exp_statuses)]

            lr = LeaveRequest(
                user_id=target_user.id,
                leave_type=l_type,
                start_date=s_date,
                end_date=e_date,
                days_count=days,
                reason=leave_reasons[i % len(leave_reasons)],
                status="PENDING" if status == "SUBMITTED" else status,
                client_uuid=client_uuid,
                rejection_reason="Team coverage unavailable on requested dates" if status == "REJECTED" else None,
            )
            db.add(lr)
            db.flush()

            appr_status = "PENDING" if status == "SUBMITTED" else status
            appr = ApprovalRequest(
                entity_type="LEAVE",
                entity_id=lr.id,
                requester_id=target_user.id,
                status=appr_status,
                title=f"Leave Request - {l_type} ({days:g} Days)",
                details=f"Requested by {target_user.full_name} from {s_date} to {e_date}. {lr.reason}",
            )
            db.add(appr)
            db.flush()
            lr.approval_request_id = appr.id

            if appr_status in ("APPROVED", "REJECTED"):
                db.add(
                    ApprovalHistory(
                        request_id=appr.id,
                        approver_id=mgr_user.id,
                        decision=appr_status,
                        comments="Leave reviewed and actioned.",
                    )
                )
        db.commit()

        # Step 13: Seed 10 Tour Programs
        logger.info("Step 13: Seeding 10 Monthly/Weekly Tour Programs...")
        tour_titles = [
            ("South Mumbai KOL Cardiology Tour", 5, "Cuffe Parade -> Nariman Point -> Marine Lines"),
            ("Bandra Suburban Chemist & Doctor Sweep", 4, "Bandra West -> Khar -> Santacruz"),
            ("Andheri West Polyclinics Coverage", 6, "Lokhandwala -> Versova -> Oshiwara"),
            ("Parel Hospital Belt Intensive TP", 5, "KEM -> Tata Memorial -> Wadia"),
            ("Pune Central Tertiary Care Drive", 5, "Deccan -> Shivajinagar -> Camp"),
            ("Pune Chinchwad Industrial Expansion", 4, "Pimpri -> Bhosari -> Nigdi"),
            ("Thane Lake City Key Prescribers", 5, "Naupada -> Panchpakhadi -> Ghodbunder"),
            ("Navi Mumbai Satellite Clinics Run", 4, "Vashi -> Nerul -> Belapur"),
            ("Delhi South Cardiology Campaign", 6, "Saket -> Greater Kailash -> Hauz Khas"),
            ("Bangalore CBD Specialist Drive", 5, "MG Road -> Indiranagar -> Koramangala"),
        ]

        for i, (title, total_days, route) in enumerate(tour_titles, start=1):
            target_user = team_mrs[i % len(team_mrs)]
            existing_tp = db.query(TourProgram).filter_by(title=title, user_id=target_user.id).first()
            if existing_tp:
                continue

            start_d = today + timedelta(days=(i * 7) - 21)
            end_d = start_d + timedelta(days=total_days - 1)
            t_status = "APPROVED" if i <= 4 else ("SUBMITTED" if i <= 8 else "DRAFT")

            tp = TourProgram(
                user_id=target_user.id,
                title=title,
                start_date=start_d,
                end_date=end_d,
                total_days=total_days,
                route_details=route,
                objectives="Intensive coverage of Tier 1 KOLs and institutional pharmacies.",
                status=t_status,
            )
            db.add(tp)
            db.flush()

            if t_status != "DRAFT":
                appr_status = "PENDING" if t_status == "SUBMITTED" else "APPROVED"
                appr = ApprovalRequest(
                    entity_type="TOUR",
                    entity_id=tp.id,
                    requester_id=target_user.id,
                    status=appr_status,
                    title=f"Tour Program - {title} ({total_days} Days)",
                    details=f"Route: {route}. Start: {start_d} to {end_d}.",
                )
                db.add(appr)
                db.flush()
                tp.approval_request_id = appr.id

                if appr_status == "APPROVED":
                    db.add(
                        ApprovalHistory(
                            request_id=appr.id,
                            approver_id=mgr_user.id,
                            decision="APPROVED",
                            comments="Tour plan aligns with territory target.",
                        )
                    )
        # 16. Seed 50 Operational Tasks & Discussion Comments
        if db.query(Task).count() < 10:
            logger.info("Seeding 50 Tasks with comments...")
            task_templates = [
                ("Deliver Orthovita promotional samples", "DOCTOR", "Deliver newly released 500mg sample batches and brochure.", "HIGH"),
                ("Collect overdue payment cheque", "CHEMIST", "Follow up on outstanding ₹24,500 invoice older than 30 days.", "URGENT"),
                ("Schedule CMO presentation meeting", "HOSPITAL", "Brief medical superintendent on institutional rate contract.", "HIGH"),
                ("Primary order replenishment discussion", "STOCKIST", "Review inventory levels of top 5 fast-moving SKUs.", "MEDIUM"),
                ("Gather feedback on Neurocalm adverse reactions", "DOCTOR", "Check patient tolerance reports from neurology OPD.", "MEDIUM"),
                ("Distribute festive gift hampers", "CHEMIST", "Deliver seasonal Diwali goodwill hampers to high-volume chemists.", "LOW"),
                ("Joint field ride-along preparation", None, "Review monthly focus brands before territory manager visit.", "MEDIUM"),
                ("Submit pending expense vouchers", None, "Collate physical toll and hotel bills for Q3 audit.", "LOW"),
                ("Doctor birthday greeting & card delivery", "DOCTOR", "Deliver customized birthday greeting card and floral bouquet.", "LOW"),
                ("Resolve stock dispute for shipment #492", "STOCKIST", "Cross-verify credit note against damaged vial returns.", "HIGH"),
            ]

            created_tasks: list[Task] = []
            for i in range(50):
                tmpl_idx = i % len(task_templates)
                title_prefix, ctype, desc, default_prio = task_templates[tmpl_idx]
                
                # Determine due date
                if i < 15:
                    # Due today
                    due_d = today
                elif i < 35:
                    # Upcoming
                    due_d = today + timedelta(days=random.randint(1, 14))
                else:
                    # Overdue
                    due_d = today - timedelta(days=random.randint(1, 10))

                # Assignment: 70% to mr_user, 30% to mgr or team MRs
                if i % 3 == 0:
                    assignee = mgr_user
                else:
                    assignee = mr_user

                # Priority distribution
                prio = random.choice(["LOW", "MEDIUM", "HIGH", "URGENT"]) if i % 2 == 0 else default_prio

                # Status
                if i % 5 == 0:
                    status = "COMPLETED"
                    completed_at = datetime.utcnow() - timedelta(hours=random.randint(2, 48))
                elif i % 4 == 0:
                    status = "IN_PROGRESS"
                    completed_at = None
                else:
                    status = "PENDING"
                    completed_at = None

                # Customer reference
                cid = None
                if ctype == "DOCTOR" and doctors:
                    doc = doctors[i % len(doctors)]
                    title = f"{title_prefix} - Dr. {doc.full_name}"
                    cid = doc.id
                elif ctype == "CHEMIST" and chemists:
                    chm = chemists[i % len(chemists)]
                    title = f"{title_prefix} - {chm.shop_name}"
                    cid = chm.id
                elif ctype == "HOSPITAL" and hospitals:
                    hosp = hospitals[i % len(hospitals)]
                    title = f"{title_prefix} - {hosp.name}"
                    cid = hosp.id
                elif ctype == "STOCKIST" and stockists:
                    stk = stockists[i % len(stockists)]
                    title = f"{title_prefix} - {stk.agency_name}"
                    cid = stk.id
                else:
                    title = f"{title_prefix} #{i + 1}"

                task = Task(
                    title=title,
                    description=desc,
                    due_date=due_d,
                    priority=prio,
                    status=status,
                    completed_at=completed_at,
                    assigned_to_id=assignee.id,
                    created_by_id=mgr_user.id if assignee.id == mr_user.id else admin_user.id,
                    customer_type=ctype,
                    customer_id=cid,
                    client_uuid=f"task-seed-{i + 1}",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                    updated_at=datetime.utcnow(),
                )
                db.add(task)
                db.flush()
                created_tasks.append(task)

                # Add 1-2 comments
                comment_texts = [
                    "Please ensure this is finished before the 4:00 PM review.",
                    "Noted sir, heading there in the afternoon session.",
                    "Spoke with the doctor's assistant, appointment confirmed for 11:30 AM.",
                    "Stock reconciliation matched with distributor ledger.",
                ]
                db.add(
                    TaskComment(
                        task_id=task.id,
                        user_id=mgr_user.id,
                        message=comment_texts[i % len(comment_texts)],
                        created_at=datetime.utcnow() - timedelta(hours=random.randint(5, 36)),
                    )
                )
                if i % 2 == 0:
                    db.add(
                        TaskComment(
                            task_id=task.id,
                            user_id=mr_user.id,
                            message=comment_texts[(i + 1) % len(comment_texts)],
                            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 4)),
                        )
                    )

        # 17. Seed In-App Notifications
        if db.query(Notification).count() < 10:
            logger.info("Seeding 25 Notifications...")
            notif_samples = [
                ("Tour Program Approved", "Your upcoming 4-day tour program to Pune has been approved by your manager.", "TOUR", False),
                ("New Task Assigned", "Urgent: Deliver Orthovita promotional samples to Dr. Rajesh Sharma.", "TASK", False),
                ("Expense Approved", "Your monthly travel & food expense claim #EXP-902 has been approved.", "EXPENSE", True),
                ("Pending Manager Approval", "3 Leave applications from your team are awaiting review.", "APPROVAL", False),
                ("Attendance Reminder", "Don't forget to mark your daily evening check-out before 8:00 PM.", "SYSTEM", False),
                ("Doctor Follow-up", "Follow-up reminder scheduled for Dr. Priya Deshmukh today.", "TASK", False),
                ("Monthly Target Update", "Territory achieved 84% of primary sales target this month. Great effort!", "SYSTEM", True),
                ("Customer Added", "A new Chemist 'MedPlus Pharmacy' was added to your territory.", "SYSTEM", True),
            ]
            for i in range(25):
                title, body, ntype, is_read = notif_samples[i % len(notif_samples)]
                target = mr_user if i % 3 != 0 else mgr_user
                db.add(
                    Notification(
                        user_id=target.id,
                        title=f"{title} #{i + 1}",
                        body=body,
                        notification_type=ntype,
                        reference_id=str(random.randint(100, 999)),
                        is_read=is_read,
                        read_at=datetime.utcnow() if is_read else None,
                        created_at=datetime.utcnow() - timedelta(hours=i * 3),
                    )
                )

        # 18. Seed Pharmaceutical Products & E-Detailing Visual Aids
        if db.query(Product).count() < 5:
            logger.info("Seeding 25 Pharmaceutical Products with E-Detailing Visual Aids...")
            products_seed_data = [
                ("DIA-001", "Diabex 500", "Diabetology", "Metformin Hydrochloride 500mg", "500mg", "10x10 Tablets", 65.0, 48.0, 44.0, "Type-2 Diabetes Mellitus, Insulin Resistance", "One tablet twice daily with meals"),
                ("DIA-002", "Diabex-M 1/500", "Diabetology", "Glimepiride 1mg + Metformin 500mg", "1mg/500mg", "10x10 Tablets", 110.0, 82.0, 75.0, "Uncontrolled Type-2 Diabetes Mellitus", "One tablet once daily before breakfast"),
                ("DIA-003", "Glipten 50", "Diabetology", "Vildagliptin 50mg", "50mg", "10x14 Tablets", 195.0, 145.0, 132.0, "Dual therapy in adults with Type-2 Diabetes", "One tablet twice daily morning & evening"),
                ("DIA-004", "Empasure 10", "Diabetology", "Empagliflozin 10mg", "10mg", "10x10 Tablets", 240.0, 180.0, 165.0, "Type-2 Diabetes with cardiovascular disease risk", "One tablet once daily with or without food"),
                ("CAR-001", "Cardipres 5", "Cardiology", "Amlodipine Besylate 5mg", "5mg", "10x10 Tablets", 55.0, 40.0, 36.0, "Essential Hypertension, Chronic Stable Angina", "5mg once daily, titrate if needed"),
                ("CAR-002", "Cardipres-AT", "Cardiology", "Amlodipine 5mg + Atenolol 50mg", "5mg/50mg", "10x10 Tablets", 98.0, 72.0, 65.0, "Moderate to Severe Hypertension", "One tablet once daily in the morning"),
                ("CAR-003", "Telmipres 40", "Cardiology", "Telmisartan 40mg", "40mg", "10x10 Tablets", 125.0, 92.0, 84.0, "Hypertension & Cardiovascular Risk Reduction", "40mg once daily with water"),
                ("CAR-004", "Rosuvast 10", "Cardiology", "Rosuvastatin Calcium 10mg", "10mg", "10x10 Tablets", 160.0, 120.0, 110.0, "Primary Hypercholesterolemia, Dyslipidemia", "One tablet once daily at bedtime"),
                ("ANT-001", "Amoxyclav 625", "Antibiotics", "Amoxicillin 500mg + Potassium Clavulanate 125mg", "625mg", "10x6 Tablets", 210.0, 160.0, 145.0, "RTI, UTI, Skin & Soft Tissue Infections", "One tablet every 12 hours after food"),
                ("ANT-002", "Cefurox 500", "Antibiotics", "Cefuroxime Axetil 500mg", "500mg", "10x10 Tablets", 450.0, 340.0, 310.0, "Upper & Lower Respiratory Tract Infections", "One tablet twice daily for 5 to 7 days"),
                ("ANT-003", "Azikem 500", "Antibiotics", "Azithromycin Dihydrate 500mg", "500mg", "10x3 Tablets", 130.0, 95.0, 86.0, "Community Acquired Pneumonia, Pharyngitis", "One tablet once daily for 3 days"),
                ("ORT-001", "Orthovita Max", "Orthopedics", "Glucosamine Sulphate 750mg + Chondroitin 100mg", "850mg", "10x10 Tablets", 280.0, 210.0, 190.0, "Osteoarthritis of knee and hip joints", "One tablet twice daily with meals"),
                ("ORT-002", "Aceclo-SP", "Orthopedics", "Aceclofenac 100mg + Paracetamol 325mg + Serratiopeptidase 15mg", "Triple Action", "10x10 Tablets", 115.0, 85.0, 77.0, "Post-traumatic pain, Rheumatoid arthritis, Dental pain", "One tablet twice daily after meals"),
                ("ORT-003", "Calcitop D3", "Orthopedics", "Calcium Carbonate 1250mg + Vitamin D3 2000 IU", "Forte", "10x15 Tablets", 175.0, 130.0, 118.0, "Osteoporosis, Calcium deficiency in elderly", "One tablet daily after breakfast"),
                ("NEU-001", "Neurocalm Plus", "Neurology", "Pregabalin 75mg + Methylcobalamin 750mcg", "75mg/750mcg", "10x10 Capsules", 220.0, 165.0, 150.0, "Diabetic Peripheral Neuropathy, Sciatica", "One capsule at bedtime"),
                ("NEU-002", "Gabamax 300", "Neurology", "Gabapentin 300mg + Mecobalamin 500mcg", "300mg", "10x10 Tablets", 260.0, 195.0, 178.0, "Post-herpetic Neuralgia, Neuropathic Pain", "One tablet three times daily"),
                ("GAS-001", "Pantop 40", "Gastroenterology", "Pantoprazole Sodium 40mg", "40mg", "10x10 Tablets", 95.0, 70.0, 63.0, "GERD, Erosive Esophagitis, Peptic Ulcers", "One tablet daily before breakfast"),
                ("GAS-002", "Pantop-DSR", "Gastroenterology", "Pantoprazole 40mg + Domperidone 30mg SR", "Sustained Release", "10x10 Capsules", 165.0, 125.0, 112.0, "Acid Reflux with Nausea, Dyspepsia", "One capsule early morning on empty stomach"),
                ("GAS-003", "Sucraheal-O", "Gastroenterology", "Sucralfate 1000mg + Oxetacaine 20mg Suspension", "1000mg/20mg", "200ml Bottle", 185.0, 140.0, 126.0, "Duodenal ulcer, Stress ulcer, Gastric burn", "Two teaspoons 1 hour before meals"),
                ("RES-001", "Montair-LC", "Respiratory", "Montelukast 10mg + Levocetirizine 5mg", "10mg/5mg", "10x10 Tablets", 175.0, 130.0, 118.0, "Allergic Rhinitis, Seasonal Allergies", "One tablet at bedtime"),
            ]

            created_products: list[Product] = []
            for code, name, cat, comp, strn, pkg, mrp, ptr, pts, ind, dose in products_seed_data:
                p = Product(
                    code=code,
                    name=name,
                    brand="Mediate Healthcare",
                    category=cat,
                    composition=comp,
                    strength=strn,
                    packaging=pkg,
                    mrp=mrp,
                    ptr=ptr,
                    pts=pts,
                    gst_rate=12.0,
                    indications=ind,
                    dosage_guidelines=dose,
                    is_sample_available=True,
                    is_active=True,
                )
                db.add(p)
                db.flush()
                created_products.append(p)

                # Add 2 visual aid presentation slides per product
                slide1 = ProductVisualAid(
                    product_id=p.id,
                    title=f"Clinical Efficacy & Action of {name}",
                    image_url=None,
                    slide_order=1,
                    key_talk_points=f"• Proven 24-hr clinical effectiveness\n• Superior bioavailability: {comp}\n• Indicated for {ind}",
                )
                slide2 = ProductVisualAid(
                    product_id=p.id,
                    title=f"Dosage & Patient Safety Profile - {name}",
                    image_url=None,
                    slide_order=2,
                    key_talk_points=f"• Standard prescription: {dose}\n• Well tolerated in clinical trials with high compliance",
                )
                db.add(slide1)
                db.add(slide2)

        # 19. Seed Commercial Orders
        if db.query(Order).count() < 5 and db.query(Product).count() > 0:
            logger.info("Seeding 20 Commercial Orders...")
            all_prods = db.query(Product).all()
            for idx in range(20):
                is_chemist = idx % 2 == 0
                ctype = "CHEMIST" if is_chemist else "STOCKIST"
                cid = chemists[idx % len(chemists)].id if is_chemist and chemists else stockists[idx % len(stockists)].id
                
                # Pick 2-4 products
                num_items = random.randint(2, 4)
                chosen_prods = random.sample(all_prods, min(num_items, len(all_prods)))
                
                order_num = f"ORD-202610-{(1000 + idx)}"
                st = "CONFIRMED" if idx % 3 == 0 else ("DELIVERED" if idx % 4 == 0 else "SUBMITTED")
                
                tot = 0.0
                order_items_to_add = []
                for pr in chosen_prods:
                    qty = random.randint(5, 30) * 10
                    unit_p = pr.ptr if is_chemist else pr.pts
                    l_tot = round(qty * unit_p, 2)
                    tot += l_tot
                    order_items_to_add.append(
                        OrderItem(
                            product_id=pr.id,
                            quantity=qty,
                            unit_price=unit_p,
                            total_price=l_tot,
                            free_quantity=qty // 10,
                        )
                    )

                ord_obj = Order(
                    order_number=order_num,
                    customer_type=ctype,
                    customer_id=cid,
                    user_id=mr_user.id if idx % 3 != 0 else mgr_user.id,
                    total_amount=round(tot, 2),
                    status=st,
                    expected_delivery_date=today + timedelta(days=random.randint(2, 7)),
                    payment_terms="Net 30 Days" if not is_chemist else "Cheque on Delivery",
                    notes=f"Primary order for Q4 stock replenishment. Dispatch via local courier.",
                    items=order_items_to_add,
                )
                db.add(ord_obj)

        db.commit()

        logger.info("=======================================================")
        logger.info("RICH SEEDING COMPLETE!")
        logger.info("Doctors:        %d", db.query(Doctor).count())
        logger.info("Chemists:       %d", db.query(Chemist).count())
        logger.info("Hospitals:      %d", db.query(Hospital).count())
        logger.info("Stockists:      %d", db.query(Stockist).count())
        logger.info("Territories:    %d", db.query(Territory).count())
        logger.info("Planned Visits: %d", db.query(PlannedVisit).count())
        logger.info("DCR Visits:     %d", db.query(DcrVisit).count())
        logger.info("Follow-ups:     %d", db.query(FollowUp).count())
        logger.info("Expenses:       %d", db.query(Expense).count())
        logger.info("Leaves:         %d", db.query(LeaveRequest).count())
        logger.info("Approvals:      %d", db.query(ApprovalRequest).count())
        logger.info("Tour Programs:  %d", db.query(TourProgram).count())
        logger.info("=======================================================")

    except Exception as exc:
        db.rollback()
        logger.exception("Error during rich seeding: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_rich_data()
