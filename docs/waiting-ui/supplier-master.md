# Supplier Master - Waiting UI Specification

**Status**: `WAITING_UI` / `PROVISIONAL`
**Route**: `/masters/customers/supplier`
**Backend Endpoint**: `/api/v1/masters?type=SUPPLIER`

## Context & Probable Purpose
In pharmaceutical field operations and ERP distributions, a **Supplier Master** tracks manufacturing entities, C&F (Consignment & Forwarding) agents, primary distributors, or third-party drug manufacturers from whom pharmaceutical products and samples originate.

Currently, this master has been initialized with generic fields (`code`, `name`, `description`, `is_provisional=True`).

## Questions Needed from Project Owner / Reference Screens
1. **Field-level Information**:
   - What specific identifiers are mandatory: Drug License No (DL No), GSTIN, PAN, TAN?
   - Is contact person details required (Contact Person Name, Phone, Email, Billing Address, Shipping Address)?
2. **Category / Type**:
   - Is there a supplier categorization (e.g., Own Manufacturing Unit, Third-Party Loan Licensee, Import Partner, C&F Agent)?
3. **Credit Terms & Lead Times**:
   - Are standard payment terms (e.g., Net 30, Advance) and delivery lead times (in days) maintained at the supplier level?
4. **Integration**:
   - Does this master link directly with Sample Stock Inward (Wave W8) and Purchase Inward?

Until reference screenshots and field specifications are provided, this master operates with standard generic master fields and is marked with a **Provisional** badge.
