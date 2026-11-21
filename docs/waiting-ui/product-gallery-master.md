# Product Gallery Master - Waiting UI Specification

**Status**: `WAITING_UI` / `PROVISIONAL`
**Route**: `/masters/products/gallery`
**Backend Endpoint**: `/api/v1/masters?type=PRODUCT_GALLERY`

## Context & Probable Purpose
In modern medical representative (MR) digital detailing (e-detailing), the **Product Gallery Master** serves as a repository of visual aids, 3D packaging renderings, mechanism-of-action (MOA) animation slides, and clinical trial comparative study slides shown to doctors during in-clinic visits.

Currently, this master has been initialized with generic fields (`code`, `name`, `description`, `is_provisional=True`).

## Questions Needed from Project Owner / Reference Screens
1. **Digital Asset Properties**:
   - Does each gallery slide link directly to a specific product (`product_id`)?
   - What file formats are supported (PDF visual aids, MP4 animations, PNG/JPG high-resolution pack shots, HTML5 interactive slides)?
2. **Detailing Hierarchy**:
   - Are slides grouped into sequences or stories (e.g., Detailing Storyboard: Problem Statement -> MOA -> Clinical Efficacy -> Dosage & Packaging)?
3. **Target Audience**:
   - Can slides be tagged to specific doctor specialities (e.g., show slide only to Cardiologists vs Diabetologists)?
4. **Analytics / Telemetry**:
   - Should the system track presentation time per slide during e-detailing visits?

Until reference screenshots and detailed visual asset schemas are provided, this master operates with standard generic master fields and is marked with a **Provisional** badge.
