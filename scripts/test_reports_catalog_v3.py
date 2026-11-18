"""Integration test for Reports Catalog v3 endpoints."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.modules.reports.service import ReportService
from app.core.scope import ScopeContext, UserRole
from app.modules.reports.schemas import ReportRunRequest, ReportExportRequest
from app.modules.users.models import User

def main():
    session = SessionLocal()
    admin_user = session.query(User).filter(User.email == "admin@mediatehealthcare.com").first()
    assert admin_user is not None, "Admin user must exist"

    service = ReportService(session)
    context = ScopeContext(
        user_id=admin_user.id,
        role=UserRole.ADMIN,
        territory_id=None,
        team_member_ids=[],
    )

    print("--- 1. Testing GET /reports (Catalog v3) ---")
    cat = service.get_catalog_v3(context=context, page_size=100)
    print(f"Catalog total reports: {cat.total}, Groups: {cat.groups}")
    assert cat.total == 48, f"Expected 48 reports, got {cat.total}"
    assert len(cat.items) == 48, f"Expected 48 items, got {len(cat.items)}"

    print("--- 2. Testing GET /reports/{key} ---")
    dcr_def = service.get_definition_v3("daily_call_report", context)
    print(f"Definition: {dcr_def.name} | Status: {dcr_def.status}")
    assert dcr_def.status == "AVAILABLE"
    assert dcr_def.filter_schema is not None

    track_def = service.get_definition_v3("track_report", context)
    print(f"Coming Soon Definition: {track_def.name} | Status: {track_def.status} | Reason: {track_def.unavailable_reason}")
    assert track_def.status == "COMING_SOON"

    print("--- 3. Testing GET /reports/options/states ---")
    opts = service.get_options("states", context)
    print(f"Options for states: {opts.total} options found ({[o.label for o in opts.options[:3]]})")
    assert opts.total > 0

    print("--- 4. Testing POST /reports/daily_call_report/run ---")
    run_req = ReportRunRequest(
        filters={"month": "11", "year": 2026, "status": "ALL"},
        page=1,
        page_size=20,
    )
    run_res = service.run_report_v3("daily_call_report", run_req, context, admin_user)
    print(f"Run Result: total rows={run_res.total}, summary={run_res.summary}")
    print(f"Columns: {[c.label for c in run_res.columns]}")

    print("--- 5. Testing POST /reports/daily_call_report/export (XLSX) ---")
    exp_req = ReportExportRequest(filters={"month": "11", "year": 2026, "status": "ALL"})
    xlsx_bytes, fname_xlsx, m_type_xlsx = service.export_report_v3("daily_call_report", exp_req, "xlsx", context, admin_user)
    print(f"Exported XLSX: {fname_xlsx} ({len(xlsx_bytes)} bytes)")
    assert len(xlsx_bytes) > 0

    print("--- 6. Testing POST /reports/daily_call_report/export (PDF) ---")
    pdf_bytes, fname_pdf, m_type_pdf = service.export_report_v3("daily_call_report", exp_req, "pdf", context, admin_user)
    print(f"Exported PDF: {fname_pdf} ({len(pdf_bytes)} bytes)")
    assert pdf_bytes.startswith(b"%PDF"), "PDF file must start with %PDF"

    print("\n✅ ALL BACKEND CATALOG V3 TESTS PASSED!")

if __name__ == "__main__":
    main()
