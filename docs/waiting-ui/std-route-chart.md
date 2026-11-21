# Standard Route Chart (WAITING_UI Specification)

**Module:** Standard Route Chart (`/utility/manage-routes/std-route-chart`)  
**Status:** `WAITING_UI`  
**Classification:** Group D Utility (Operational Route Master)  

---

## 1. Context & Overview
In traditional MR field operations portals, a "Standard Route Chart" (often abbreviated as SRC) defines pre-authorized travel routes, travel allowances, and standard distance benchmarks between headquarters, ex-stations, and out-stations.

Reference inspection identified a 3-tile status workflow (`Drafts`, `Applied`, `Received`) with routes linked between employees and territories, but detailed form specifications, travel modes, and computational rules were not provided.

---

## 2. Open Design & Implementation Questions for Stakeholder / Product Owner

1. **Route Header & Leg Fields**:
   - Does a standard route consist of a single Origin-Destination pair (From City -> To City) or an ordered multi-stop itinerary (From Town -> Via Town 1 -> Via Town 2 -> To Town)?
   - Are standard travel distances (in kilometers) auto-calculated via Google Maps / GPS matrix, or entered manually by the administrator?

2. **Travel Modes & Fare Rates**:
   - Does each route specify pre-approved travel modes (e.g. Bus, Train 2nd Class, Two-Wheeler @ ₹3.50/km, Four-Wheeler)?
   - Are daily allowances (DA) determined by standard route type (HQ, Ex-Station, Out-Station)?

3. **Approval Lifecycle**:
   - The reference shows Drafts, Applied, and Received workflow tiles.
   - Who initiates the route chart (MR requests new route or Admin creates master)?
   - Does route approval require Area Business Manager (ABM) or Regional Business Manager (RBM) multi-level signoff?

4. **Employee & Territory Mapping ("From / To Employee")**:
   - What is the business meaning of "From Employee" and "To Employee"? Is this a route transfer utility (handing over an established route from a departing MR to a new MR), or a joint working route definition?

---

## 3. Temporary System Handling
Until UI screenshots and business answers are confirmed:
- The route `/utility/manage-routes/std-route-chart` displays a clean `ComingSoon` component in the Web Portal with status `WAITING_UI`.
- No speculative schema or mock data will be deployed into production.
