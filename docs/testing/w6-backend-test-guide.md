# Wave W6 Backend Manual Test Guide

This guide provides step-by-step verification instructions for QA and project owners to test Wave W6 backend endpoints directly via Swagger UI or curl.

---

## 1. Authentication
1. Navigate to `http://localhost:8000/docs` (Swagger UI).
2. Click **Authorize** and login using:
   - **Admin**: `admin@mediatehealthcare.com` / `Admin@123`
   - **Manager**: `manager@mediatehealthcare.com` / `Manager@123`
   - **MR**: `mr@mediatehealthcare.com` / `Mr@123`

---

## 2. Testing Company Profile (Application Setting)
1. **GET `/api/v1/company-profile`**:
   - Send GET request as Admin.
   - Expected: HTTP 200 with `company_name: "Mediate Healthcare Pvt. Ltd."`, `company_code: "MED-HQ"`, address, phone, and null logo/signature URLs until uploaded.
2. **PUT `/api/v1/company-profile`**:
   - Send PUT request with updated phone or address.
   - Expected: HTTP 200 with updated fields.
3. **Public Branding**:
   - Call `GET /api/v1/auth/config` without login.
   - Expected: HTTP 200 with `company_name`, `company_code`, and `logo_url`.

---

## 3. Testing Provisional Masters & Confirm Endpoints
1. **GET `/api/v1/masters?type=ATTACHMENT_TYPE`**:
   - Expected: HTTP 200 with list of seeded documents (PAN, Aadhaar, Drug License) each having `is_provisional: true`.
2. **POST `/api/v1/masters/ATTACHMENT_TYPE/{id}/confirm`**:
   - Confirm item #{id}.
   - Expected: HTTP 200 with `is_provisional: false`.
3. **POST `/api/v1/masters/ATTACHMENT_TYPE/confirm-bulk`**:
   - Pass `{"item_ids": [1, 2, 3]}`.
   - Expected: HTTP 200 returning list of confirmed items with `is_provisional: false`.

---

## 4. Testing Meetings Workflow Inbox
1. **GET `/api/v1/meetings/summary`**:
   - Expected: HTTP 200 with `{ "drafts": X, "applied": Y, "received": Z, "total": N }`.
2. **POST `/api/v1/meetings`**:
   - Create a draft meeting:
     ```json
     {
       "agenda": "Cycle Review Q4",
       "meeting_type": "CYCLE_MEETING",
       "start_date": "2026-12-05T10:00:00",
       "end_date": "2026-12-05T13:00:00",
       "status": "DRAFT"
     }
     ```
   - Expected: HTTP 201 Created with status `DRAFT`.
3. **POST `/api/v1/meetings/{id}/submit`**:
   - Expected: HTTP 200 with status `APPLIED`.
4. **POST `/api/v1/meetings/{id}/approve`**:
   - Call as Admin.
   - Expected: HTTP 200 with status `APPROVED`.

---

## 5. Testing Unified Calendar Month View
1. **GET `/api/v1/calendar/month?year=2026&month=11`**:
   - Send request as Admin or Manager.
   - Expected: HTTP 200 returning 30 days for November 2026.
   - In each day object:
     - `counts`: `doctor`, `chemist`, `stockist`, `new_doctor`, `new_chemist`, `new_stockist`, `total_pob`.
     - `events`: includes Sunday weekly offs, tour plans, leaves, and scheduled meetings.
