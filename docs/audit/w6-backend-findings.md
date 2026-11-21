# Wave W6 Backend Findings Report

**Date**: 2026-11-21  
**Author**: Antigravity  
**Repository**: `Mediateappbackend-api`  

---

## 1. Drill-Down Correctness & 16 Metrics Verification

As proven by the test suite `tests/test_w6_regressions.py::test_16_metrics_card_count_equals_detail_rows`:
- For all 16 canonical Visits Summary metrics (`chemist_visits`, `new_chemist_visits`, `doctor_visits`, `new_doctor_visits`, `stockist_visits`, `new_stockist_visits`, `doctor_call_average`, `missing_doctor`, `punch_in_time`, `first_call_time`, `last_call_time`, `punch_out_time`, `morning_calls`, `evening_calls`, `work_duration`, `total_pob`), the summary card count values exactly match the total count of detail rows returned by `get_metric_drilldown`.
- Both `TABLE` kind (paginated customer call rows), `RECORD` kind (GPS map coordinates and metadata fields), and `TIMELINE` kind (attendance and call sequence timeline) return valid schema structures conforming to `MetricDetailResponse`.

---

## 2. Terminology Analysis: "Visit Type" vs "Call Type"

### Root Cause of Previous Runtime AttributeError
During runtime drilldown on `chemist_visits`, `doctor_visits`, and `stockist_visits`, the backend raised:
```
AttributeError: 'DcrVisit' object has no attribute 'call_type'. Did you mean: 'call_time'?
```

### Analysis of Database Models & Masters
1. **DCR Model (`app/modules/dcr/models.py`)**:
   - Class `DcrVisit`:
     - Column `visit_type`: `Mapped[str] = mapped_column(String(50), nullable=True)` storing visit category (e.g., "Regular", "Joint", "Camp", "Special").
     - Column `call_time`: `Mapped[datetime] = mapped_column(DateTime, nullable=True)` storing the timestamp of when the call was performed.
     - There is **no column named `call_type`** on `DcrVisit`.
2. **Master Items (`app/modules/masters/seed.py`)**:
   - `type = "VISIT_TYPE"`: Stores values such as `REGULAR` ("Regular Visit"), `JOINT` ("Joint Working with Manager"), `CAMP` ("Medical Camp / Screening"), `SPECIAL` ("Special KOL Meeting").
   - `type = "DOCTOR_MEETING_TYPE"`: Stores call window slots (e.g. `AFTER_2` - "After 2 O'clock meeting slot").
3. **Pharma Industry vs Database Nomenclature**:
   - In field pharma parlance, MRs and Area Managers interchangeably say "Doctor Calls" and "Doctor Visits", and refer to call category as "Call Type" (e.g., promotional call, reminder call, sample drop call).
   - In our relational schema (`dbo.dcr_visits`), the column was explicitly defined as `visit_type`.
   - The drilldown handlers (`chemist_visits.py`, `doctor_visits.py`, `stockist_visits.py`) mistakenly referenced `v.call_type` instead of `v.visit_type`.
4. **Resolution**:
   - All references have been standardized to `v.visit_type or "Regular"`.
   - As mandated by Wave Rules, **no database column renames were made**, preserving backwards database compatibility and schema contracts.
