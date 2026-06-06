# Needs Request Module
## Future University LIMS — Developer Documentation
**Version:** 1.0  
**Status:** Complete — ready for integration  
**Module path:** `backend/apps/needs/`  

---

## 1. What This Module Does

The Needs Request module implements **demand-driven procurement** —
because the lab starts empty, users submit what they need,
admin approves, and the system generates procurement documents.

### Full flow:

User submits form → System saves NeedsRequest (status: submitted)
→ Admin runs consolidation
→ ConsolidatedRequest created (groups same items)
→ Admin approves/rejects
→ Approved items move to procurement
→ Items arrive → stock updated
→ Users notified

---

## 2. Files in This Module

| File | Purpose |
|---|---|
| `models.py` | 3 database tables — CatalogueItem, NeedsRequest, ConsolidatedRequest |
| `serializers.py` | 6 serializers — converts models to/from JSON |
| `views.py` | 3 ViewSets — API logic for all endpoints |
| `urls.py` | URL routing — registers 3 API routes |

---

## 3. Database Models

### CatalogueItem
The master list of all lab items. Seeded from:
`catalogue/lab_sys_master_catalogue_enriched.xlsx`

Key fields:
- `item_code` — unique internal code (e.g. `CHEM-001`)
- `cas_number` — global chemical ID (e.g. `64-19-7`)
- `ghs_hazard_codes` — safety codes (e.g. `H226, H314`)
- `storage_condition` — where to store it
- `study_programs` — which programs use it

### NeedsRequest
One request from one user for one item.

Status lifecycle:
draft → submitted → consolidated → approved/partial/rejected → ordered → received

### ConsolidatedRequest
Groups multiple NeedsRequests for the same item.
Created automatically by the consolidation engine.

---

## 4. API Endpoints

### Catalogue
| Method | URL | Description |
|---|---|---|
| GET | `/api/catalogue/` | List all active items |
| GET | `/api/catalogue/{id}/` | Single item detail |
| GET | `/api/catalogue/search/?q=acetic` | Live search (min 2 chars) |
| GET | `/api/catalogue/categories/` | List all categories |

### Needs Requests
| Method | URL | Who |
|---|---|---|
| GET | `/api/needs/` | Admin: all · User: own only |
| POST | `/api/needs/` | Any authenticated user |
| GET | `/api/needs/{id}/` | Owner or admin |
| DELETE | `/api/needs/{id}/` | Admin only (draft status only) |
| GET | `/api/needs/my-requests/` | Current user's requests |
| GET | `/api/needs/summary/` | Admin dashboard counts |

### Consolidated Requests
| Method | URL | Who |
|---|---|---|
| GET | `/api/consolidated/` | Admin/Technician only |
| GET | `/api/consolidated/{id}/` | Admin/Technician only |
| POST | `/api/consolidated/consolidate/` | Admin — runs consolidation engine |
| POST | `/api/consolidated/{id}/approve/` | Admin — approve/partial/reject |

---

## 5. Request & Response Examples

### Submit a needs request
```json
POST /api/needs/
{
  "catalogue_item_id": "uuid-here",
  "quantity_requested": 500,
  "unit": "mL",
  "reason": "Required for microbiology practical — staining procedure",
  "floor": "2",
  "lab_room": "Lab Microbiology 2A",
  "study_program": "Biomedical",
  "urgency": "medium",
  "date_needed": "2025-09-01"
}
```

Response:
```json
{
  "id": "uuid",
  "request_code": "NR-2025-0001",
  "status": "submitted",
  "catalogue_item": {
    "common_name": "Crystal violet",
    "cas_number": "548-62-9",
    "ghs_pictograms": "Harmful, Environmental",
    "storage_condition": "Dry storage"
  },
  "quantity_requested": "500.00",
  "unit": "mL",
  "created_at": "2025-08-01T10:00:00Z"
}
```

### Run consolidation (admin)
```json
POST /api/consolidated/consolidate/
{}

Response:
{
  "detail": "Consolidation complete.",
  "created": 5,
  "updated": 2,
  "total_items": 7
}
```

### Approve a consolidated request (admin)
```json
POST /api/consolidated/{id}/approve/
{
  "action": "approve",
  "admin_notes": "Approved — budget available Q3"
}
```

### Partial approval (admin)
```json
POST /api/consolidated/{id}/approve/
{
  "action": "partial",
  "approved_quantity": 250,
  "admin_notes": "Only 250mL available in budget this month"
}
```

### Reject (admin)
```json
POST /api/consolidated/{id}/approve/
{
  "action": "reject",
  "rejection_reason": "Item already available in Lab 3 — please check shared stock"
}
```

---

## 6. Frontend Component

**File:** `frontend/src/pages/NeedsRequest/index.jsx`

Features:
- Live catalogue search with 300ms debounce
- Auto-displays CAS number, GHS hazard badges, storage condition
- 4-section form: Item · Quantity · Location · Timeline
- Urgency selector with colour coding
- Client-side validation before submit
- Success screen with tracking code

To run the frontend locally:
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## 7. How to Seed the Catalogue

The master catalogue Excel file must be imported into the database
before users can search for items.

Run this management command (to be built in Phase 3):
```bash
cd backend
python manage.py seed_catalogue \
  --file ../catalogue/lab_sys_master_catalogue_enriched.xlsx
```

This will:
1. Read the Master Catalogue and Reagent Master sheets
2. Create CatalogueItem records for all active items
3. Skip duplicates (based on item_code)
4. Report how many items were imported

---

## 8. Next Steps for Thesis Students

After setting up this module, the next modules to build
following the exact same pattern are:

1. **Booking module** — `backend/apps/booking/`
   - Models: LabRoom, Equipment, Booking
   - Same CRUD pattern as NeedsRequest
   - Add conflict detection logic in views.py

2. **Procurement module** — `backend/apps/procurement/`
   - Models: PurchaseOrder, POLineItem, GoodsReceipt
   - Triggered by approved ConsolidatedRequests
   - Generates PDF purchase order document

3. **Inventory module** — `backend/apps/inventory/`
   - Models: StockItem, StockMovement, StockAlert
   - Updated automatically on goods receipt
   - Triggers reorder when below minimum

Each module follows this exact file structure:
apps/
└── module_name/
├── __init__.py
├── models.py       ← database tables
├── serializers.py  ← JSON conversion
├── views.py        ← API logic
└── urls.py         ← URL routing

---

## 9. Testing Checklist

Before handing to production, verify:

- [ ] Catalogue search returns results for "acetic"
- [ ] Selecting item auto-fills unit field
- [ ] GHS badges display correctly for hazardous items
- [ ] Cannot submit without selecting catalogue item
- [ ] Cannot submit with past date
- [ ] Request code generated as NR-YYYY-XXXX
- [ ] Admin can run consolidation
- [ ] Admin can approve, partially approve, reject
- [ ] Rejected requests show rejection reason to user
- [ ] Non-admin users cannot access /api/consolidated/

---

*Future University LIMS — Module Documentation*  
*Built with Django REST Framework + React*  
*Repository: D:\lab_sys*
