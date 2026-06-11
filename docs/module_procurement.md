# Procurement Module
## Future University LIMS — Developer Documentation
**Version:** 1.0  
**Status:** Initial — scaffold complete  
**Module path:** `backend/apps/procurement/`

---

## 1. What This Module Does

The Procurement module manages **purchase orders, vendor logistics, and goods receipt** —
it converts approved needs requests into purchase orders and tracks delivery.

### Full flow:

Approved ConsolidatedRequest → Admin creates Purchase Order
→ PO submitted to vendor → Vendor confirms & ships
→ Goods arrive → GoodsReceipt created
→ Stock updated in Inventory module (future)
→ PO marked received

---

## 2. Files in This Module

| File | Purpose |
|---|---|
| `models.py` | 4 database tables — PurchaseOrder, POLineItem, GoodsReceipt, GoodsReceiptLine |
| `serializers.py` | 5 serializers — converts models to/from JSON |
| `views.py` | 3 ViewSets — API logic for all endpoints |
| `urls.py` | URL routing — registers 3 API routes |
| `admin.py` | Django admin registration for all models |

---

## 3. Database Models

### PurchaseOrder
A purchase order issued to a vendor.

Key fields:
- `po_number` — auto-generated (e.g. `PO-2026-0001`)
- `vendor_name` — supplier name
- `status` — draft → submitted → confirmed → shipped → partial → received → cancelled

### POLineItem
A single line item within a purchase order.

- Links to `ConsolidatedRequest` from the needs module
- Auto-calculates `total_price` from `unit_price × quantity_ordered`

### GoodsReceipt
Records when items arrive.

- Links to the parent `PurchaseOrder`
- Auto-generates receipt number (e.g. `GR-2026-0001`)

### GoodsReceiptLine
Individual line items within a goods receipt.

- Records exact quantity received per PO line item
- Updates PO line item `quantity_received` on save

---

## 4. API Endpoints

### Purchase Orders
| Method | URL | Who |
|---|---|---|
| GET | `/api/purchase-orders/` | All authenticated users |
| POST | `/api/purchase-orders/` | Admin/Technician only |
| GET | `/api/purchase-orders/{id}/` | Owner or admin |
| PUT | `/api/purchase-orders/{id}/` | Admin/Technician only |
| DELETE | `/api/purchase-orders/{id}/` | Admin/Technician only (draft only) |
| POST | `/api/purchase-orders/{id}/submit/` | Submit draft to vendor |
| POST | `/api/purchase-orders/{id}/cancel/` | Cancel a PO |
| GET | `/api/purchase-orders/summary/` | Admin dashboard counts |

### PO Line Items
| Method | URL | Who |
|---|---|---|
| GET | `/api/po-line-items/` | Admin/Technician only |
| POST | `/api/po-line-items/` | Admin/Technician only |
| GET | `/api/po-line-items/?purchase_order={id}` | Filter by PO |

### Goods Receipt
| Method | URL | Who |
|---|---|---|
| GET | `/api/goods-receipt/` | Admin/Technician only |
| POST | `/api/goods-receipt/` | Admin/Technician only |
| GET | `/api/goods-receipt/{id}/` | Admin/Technician only |
| POST | `/api/goods-receipt/{id}/receive-line/` | Record receipt of a line item |

---

## 5. Request & Response Examples

### Create a purchase order
```json
POST /api/purchase-orders/
{
  "vendor_name": "PT Sigma Aldrich Indonesia",
  "vendor_contact": "021-555-0199",
  "notes": "Urgent — needed for Q3 practical sessions",
  "expected_date": "2026-08-15",
  "total_amount": 12500000
}
```

### Submit a PO
```json
POST /api/purchase-orders/{id}/submit/
{}
```

### Record goods receipt
```json
POST /api/goods-receipt/
{
  "purchase_order": "po-uuid-here",
  "delivery_note": "DN-2026-0042",
  "notes": "All items in good condition"
}
```

---

## 6. Frontend Component

**File:** `frontend/src/pages/Procurement/index.jsx`

Features:
- Lists all purchase orders with status badges
- Token-authenticated API calls
- Tab-based navigation (Orders / Receive Goods)
- Styled consistently with Booking and NeedsRequest pages

---

## 7. Integration Points

This module integrates with:

1. **Needs Module** — `POLineItem.consolidated_request` FK to `ConsolidatedRequest`
2. **Inventory Module** (future) — Goods receipt triggers stock updates
3. **Booking Module** — None directly, but procurement enables lab operations

---

## 8. Testing Checklist

- [ ] Can create a Purchase Order via API
- [ ] PO number auto-generates as PO-YYYY-XXXX
- [ ] Can submit a draft PO
- [ ] Cannot submit a non-draft PO
- [ ] Can cancel a PO
- [ ] Cannot cancel a received PO
- [ ] Goods receipt updates PO status to partial/received
- [ ] Goods receipt line updates POLineItem quantity_received
- [ ] Non-admin users cannot create/edit POs

---

*Future University LIMS — Module Documentation*  
*Built with Django REST Framework + React*  
*Repository: D:\lab_sys*
