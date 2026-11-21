"""Seeder for Field Attendance (110+ records ensuring >= 35 for each status & mock filter)."""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.attendance.models import Attendance
from app.modules.users.models import User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="attendances")
    if not dev:
        return result

    users = session.query(User).filter(User.is_active == True).all()  # noqa: E712
    if not users:
        return result

    today = date.today()

    locations = [
        {"addr": "Connaught Place, Central Delhi, Delhi - 110001", "lat": 28.6315, "lng": 77.2167},
        {"addr": "Bandra Kurla Complex, Mumbai, Maharashtra - 400051", "lat": 19.0674, "lng": 72.8687},
        {"addr": "Indiranagar 100 Feet Road, Bengaluru, Karnataka - 560038", "lat": 12.9784, "lng": 77.6408},
        {"addr": "Banjara Hills Road No 12, Hyderabad, Telangana - 500034", "lat": 17.4156, "lng": 78.4350},
        {"addr": "Park Street Commercial Area, Kolkata, West Bengal - 700016", "lat": 22.5510, "lng": 88.3526},
        {"addr": "Anna Nagar West Extension, Chennai, Tamil Nadu - 600101", "lat": 13.0850, "lng": 80.2101},
        {"addr": "C.G. Road Navrangpura, Ahmedabad, Gujarat - 380009", "lat": 23.0373, "lng": 72.5562},
        {"addr": "FC Road Shivajinagar, Pune, Maharashtra - 411004", "lat": 18.5284, "lng": 73.8441},
        {"addr": "Hazratganj Main Market, Lucknow, Uttar Pradesh - 226001", "lat": 26.8467, "lng": 80.9462},
        {"addr": "MI Road Gopalbari, Jaipur, Rajasthan - 302001", "lat": 26.9168, "lng": 75.8016},
        {"addr": "Sector 17 Commercial Complex, Chandigarh - 160017", "lat": 30.7398, "lng": 76.7827},
        {"addr": "Bistupur Main Road, Jamshedpur, Jharkhand - 831001", "lat": 22.7989, "lng": 86.1865},
    ]

    # Generate 110 attendance records:
    # idx 0..44: Clean PRESENT (45 records)
    # idx 45..79: HALF_DAY (35 records)
    # idx 80..114: Mock GPS flagged (35 records)
    total_records = 115
    for idx in range(total_records):
        u = users[idx % len(users)]
        # Distribute over past 14 days
        day_offset = (idx // len(users)) + (idx % 7)
        rec_date = today - timedelta(days=day_offset)
        loc = locations[idx % len(locations)]

        client_uuid = f"seed-att-{u.id}-{rec_date.isoformat()}-{idx}"

        existing = session.query(Attendance).filter(
            (Attendance.client_uuid == client_uuid) |
            ((Attendance.user_id == u.id) & (Attendance.date == rec_date))
        ).first()

        # Categorize to guarantee >= 35 records for every category
        if idx < 45:
            # 1. Clean PRESENT
            status_val = "PRESENT"
            is_mock = False
            in_hour = 9
            in_min = 10 + (idx % 25)
            out_hour = 18
            out_min = 15 + (idx % 30)
            work_mins = (out_hour - in_hour) * 60 + (out_min - in_min)
            remarks = f"Regular field duties in assigned beat - {u.full_name}."
        elif idx < 80:
            # 2. HALF_DAY (35 records)
            status_val = "HALF_DAY"
            is_mock = False
            in_hour = 9
            in_min = 15 + (idx % 20)
            out_hour = 13
            out_min = 30 + (idx % 15)
            work_mins = (out_hour - in_hour) * 60 + (out_min - in_min)
            remarks = "Half-day shift completed - doctor calls attended."
        else:
            # 3. MOCK GPS TAMPERING (35 records)
            status_val = "PRESENT" if idx % 2 == 0 else "HALF_DAY"
            is_mock = True
            in_hour = 9
            in_min = 5 + (idx % 20)
            out_hour = 18 if status_val == "PRESENT" else 13
            out_min = 20
            work_mins = (out_hour - in_hour) * 60 + (out_min - in_min)
            remarks = "GPS discrepancy flagged: Telemetry coordinates mismatched cellular cell tower location."

        check_in_time = datetime(rec_date.year, rec_date.month, rec_date.day, in_hour, in_min)
        check_out_time = datetime(rec_date.year, rec_date.month, rec_date.day, out_hour, out_min)

        if not existing:
            att = Attendance(
                user_id=u.id,
                date=rec_date,
                status=status_val,
                check_in_time=check_in_time,
                check_in_latitude=loc["lat"] + (idx * 0.0005),
                check_in_longitude=loc["lng"] + (idx * 0.0005),
                check_in_address=loc["addr"],
                check_in_accuracy=12.5 + (idx % 8),
                check_in_mock_flag=is_mock,
                check_out_time=check_out_time,
                check_out_latitude=loc["lat"] + (idx * 0.0005) + 0.003,
                check_out_longitude=loc["lng"] + (idx * 0.0005) + 0.003,
                check_out_address=loc["addr"],
                check_out_accuracy=14.0,
                check_out_mock_flag=is_mock,
                total_work_minutes=work_mins,
                remarks=remarks,
                client_uuid=client_uuid,
            )
            session.add(att)
            result.created += 1
        else:
            result.unchanged += 1

    session.flush()
    return result
