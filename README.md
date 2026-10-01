# Mediate Healthcare MR Backend API

Enterprise FastAPI backend service powering the Mediate Healthcare Medical Representative (MR) field operations suite.

---

## 🏛️ Architecture & Modules

Built as a robust modular monolith following clean architecture standards (Models, Schemas, Repositories, Services, Routers).

| Module | Route Prefix | Key Functionality |
| :--- | :--- | :--- |
| **Auth & Security** | `/api/v1/auth` | Argon2 password hashing, JWT 15m access tokens, 30d rotating refresh tokens, 5-attempt rate-limiting & lockout. |
| **Users & Team** | `/api/v1/users` | Admin user CRUD, active status toggles, Manager-MR hierarchical reporting assignments (`ManagerMRAssignment`). |
| **Masters & Geo** | `/api/v1/masters` | States, Cities, Areas hierarchy, dropdown caches, and bulk dropdown endpoints. |
| **Territories** | `/api/v1/territories` | Territory definitions, area bindings, and MR territory assignments. |
| **Customers** | `/api/v1/customers` | Doctors, Chemists, Stockists, Hospitals directory with Haversine radius queries for nearby customers. |
| **Attendance & GPS** | `/api/v1/attendance` | Field punch-in / punch-out, GPS location tagging, mock-location detection, work duration calculation, 409 idempotency. |
| **DCR & Visits** | `/api/v1/dcr` | Planned visits, multi-step field call reporting with server-side geofencing, discussion notes, samples, and chemist order bookings (POB). |
| **Approvals Engine** | `/api/v1/approvals` | Multi-step request workflows, Manager Inbox with pending badges, **BR-08** mandatory rejection comment rule. |
| **Tour Program (TP)** | `/api/v1/tours` | Fortnightly/monthly beat planning, **BR-09** overlap prevention, automated manager approval linkage. |
| **Expense Claims** | `/api/v1/expenses` | Daily Allowance (DA), Travel Fare (TA), Lodging claims, receipt uploads, and monthly summary metrics. |
| **Leave Management**| `/api/v1/leaves` | Casual (CL), Sick (SL), Earned (EL) balance meters, half-day (0.5) support, **BR-09** overlap checks, **BR-10** balance deductions and cancellation reversals. |

---

## 🚀 Getting Started

### 1. Environment & Prerequisites
- Python 3.12+ (tested up to Python 3.14)
- Microsoft SQL Server (e.g. SQLEXPRESS on port 1433) or Docker container
- ODBC Driver 18 for SQL Server

Create `.env` file in the root of `Mediateappbackend-api`:
```ini
DATABASE_URL=mssql+pyodbc://sa:YourPassword@127.0.0.1,1433/mediate_healthcare?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
JWT_SECRET_KEY=your-secure-jwt-secret-key-at-least-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
ENVIRONMENT=development
```

### 2. Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

### 3. Database Migrations & Seeding
```powershell
# Run Alembic migrations
alembic upgrade head

# Seed initial roles, permissions and demo accounts
python -m app.modules.users.seed
```

### 4. Running Dev Server
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Testing & Code Quality

The backend test suite uses in-memory SQLite with `StaticPool` for fast sub-second execution without depending on external databases:

```powershell
# Run full pytest suite (35+ passing tests)
pytest -v

# Run linter checks
ruff check .

# Auto-format codebase
ruff format .
```

---

## 🔑 Default Seed Accounts

| Role | Email | Default Password |
| :--- | :--- | :--- |
| **Admin** | `admin@mediatehealthcare.com` | `Admin@12345` |
| **Manager** | `manager@mediatehealthcare.com` | `Manager@12345` |
| **Medical Rep (MR)** | `mr@mediatehealthcare.com` | `Mr@12345` |
