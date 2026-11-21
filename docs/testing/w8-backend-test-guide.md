# Wave W8 Backend Testing Guide

## Overview
Instructions for executing and validating Wave W8 Sample Inventory & Stock Management backend endpoints:
- Sample Inwards at HO
- Monthly Sample Quota Allocations
- Sample Issues & Dispatches to MRs
- Batch Expiry & Central Balance Ledgers

## Prerequisites
1. Activate virtual environment:
   ```powershell
   cd e:\Mediate\Mediateappbackend-api
   .\.venv\Scripts\Activate.ps1
   ```
2. Database: SQL Server `mediate_mr_db`.

## 1. Schema Migration & Seeding
```powershell
# Run schema migration for sample stock tables
python scripts/migrate_w8_schema.py

# Seed sample stock test data
python -c "from app.db.session import SessionLocal; from app.modules.stock.seed import seed_sample_stock; db = SessionLocal(); seed_sample_stock(db); db.close()"
```

## 2. Automated Smoke Matrix
Execute the full 344-check endpoint matrix:
```powershell
python scripts/smoke_all_endpoints.py
```
Expected output:
```text
SUMMARY: Total Checks: 344 | Failures: 0
```

## 3. Dedicated Pytest Suite
Run the Wave W8 sample stock test suite:
```powershell
pytest tests/test_w8_sample_stock.py -v
```
Tests:
1. `test_sample_inward_lifecycle_and_balance_update`: Inward validation, future expiry check, stock balance increment, duplicate challan block.
2. `test_sample_allocation_single_and_bulk`: Monthly quotas, bulk allocation.
3. `test_sample_issue_and_acknowledgment`: Stock deduction, insufficient balance block, dispatch tracking, receipt acknowledgment.
