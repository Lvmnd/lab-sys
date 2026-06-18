/**
 * Procurement/index.jsx — Purchase Order Management
 * Future University LIMS
 * Admin interface for managing purchase orders and goods receipt
 */

import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const STATUS_COLORS = {
  draft:     "#95A5A6",
  submitted: "#3498DB",
  confirmed: "#2ECC71",
  shipped:   "#F39C12",
  partial:   "#E67E22",
  received:  "#27AE60",
  cancelled: "#E74C3C",
};

const S = {
  page: {
    minHeight: "100vh",
    background: "#F4F6F9",
    fontFamily: "'Segoe UI', Arial, sans-serif",
    padding: "24px 16px",
  },
  container: { maxWidth: 960, margin: "0 auto" },
  header: {
    background: "#1F497D",
    borderRadius: 12,
    padding: "20px 28px",
    marginBottom: 24,
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  headerTitle: { color: "#fff", fontSize: 22, fontWeight: 700, margin: 0 },
  headerSub:   { color: "#BDD0E8", fontSize: 13, margin: "4px 0 0" },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "20px 24px",
    marginBottom: 16,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    border: "0.5px solid #E0E8F0",
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 600,
    color: "#1F497D",
    marginBottom: 16,
    paddingBottom: 8,
    borderBottom: "1.5px solid #DCE6F1",
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  emptyState: {
    textAlign: "center",
    padding: "40px 20px",
    color: "#999",
    fontSize: 14,
  },
  badge: (color) => ({
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    color: "#fff",
    background: color,
  }),
  row: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    marginBottom: 16,
  },
  field: { display: "flex", flexDirection: "column", gap: 6 },
  label: { fontSize: 12, fontWeight: 600, color: "#555", letterSpacing: 0.3 },
  input: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    outline: "none",
    background: "#FAFCFF",
  },
  select: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    background: "#FAFCFF",
    cursor: "pointer",
  },
  submitBtn: {
    width: "100%",
    padding: "14px",
    background: "#1F497D",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 16,
    fontWeight: 700,
    cursor: "pointer",
    transition: "background 0.2s",
  },
};

export default function ProcurementPage({ token = "" }) {
  const [activeTab, setActiveTab] = useState("orders");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`${API_BASE}/purchase-orders/`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => setOrders(Array.isArray(d) ? d : d.results || []))
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div style={S.page}>
      <div style={S.container}>
        <div style={S.header}>
          <span style={{ fontSize: 32 }}>📦</span>
          <div>
            <h1 style={S.headerTitle}>Procurement Management</h1>
            <p style={S.headerSub}>
              Future University — Purchase orders, goods receipt, and vendor management
            </p>
          </div>
        </div>

        <div style={{
          display: "flex", gap: 4, marginBottom: 20,
          background: "#fff", padding: 6, borderRadius: 10,
          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
        }}>
          {[
            { key: "orders", label: "📋 Purchase Orders" },
            { key: "receive", label: "📥 Receive Goods" },
          ].map(t => (
            <button
              key={t.key}
              style={{
                flex: 1, padding: "10px 16px", borderRadius: 8,
                border: "none",
                background: activeTab === t.key ? "#1F497D" : "transparent",
                color: activeTab === t.key ? "#fff" : "#666",
                fontWeight: activeTab === t.key ? 700 : 400,
                fontSize: 14, cursor: "pointer",
                transition: "all 0.2s",
              }}
              onClick={() => setActiveTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>📋</span> All Purchase Orders
          </div>
          {loading ? (
            <div style={S.emptyState}>Loading...</div>
          ) : orders.length === 0 ? (
            <div style={S.emptyState}>
              No purchase orders yet. Approved consolidation requests will appear here.
            </div>
          ) : (
            orders.map(po => (
              <div key={po.id} style={{
                display: "flex", alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 0", borderBottom: "0.5px solid #F0F4F8",
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#1F497D" }}>
                    {po.po_number}
                  </div>
                  <div style={{ fontSize: 13, color: "#444", marginTop: 2 }}>
                    {po.vendor_name}
                  </div>
                  <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
                    {new Date(po.created_at).toLocaleDateString("id-ID")}
                    {po.expected_date && ` · Expected: ${new Date(po.expected_date).toLocaleDateString("id-ID")}`}
                  </div>
                </div>
                <span style={S.badge(STATUS_COLORS[po.status] || "#888")}>
                  {po.status_display || po.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
