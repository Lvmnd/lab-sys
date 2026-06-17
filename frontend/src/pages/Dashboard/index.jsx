/**
 * Dashboard/index.jsx — Future University LIMS
 * Main dashboard showing system overview for lab managers
 */

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

const STATUS_COLORS = {
  ok:           "#27AE60",
  low_stock:    "#F39C12",
  out_of_stock: "#E74C3C",
  expiring_soon:"#E67E22",
  expired:      "#C0392B",
  pending:      "#F39C12",
  approved:     "#27AE60",
  rejected:     "#E74C3C",
  submitted:    "#2980B9",
  received:     "#27AE60",
};

const S = {
  page: {
    minHeight: "100vh",
    background: "#F4F6F9",
    fontFamily: "'Segoe UI', Arial, sans-serif",
    padding: "24px 16px",
  },
  container: { maxWidth: 1100, margin: "0 auto" },
  welcome: {
    background: "#1F497D",
    borderRadius: 12,
    padding: "20px 28px",
    marginBottom: 24,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  welcomeTitle: { color: "#fff", fontSize: 20, fontWeight: 700, margin: 0 },
  welcomeSub:   { color: "#BDD0E8", fontSize: 13, margin: "4px 0 0" },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 16,
    marginBottom: 24,
  },
  metricCard: (color) => ({
    background: "#fff",
    borderRadius: 12,
    padding: "20px 24px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    border: `0.5px solid #E0E8F0`,
    borderLeft: `4px solid ${color}`,
  }),
  metricNum:   { fontSize: 32, fontWeight: 700, color: "#1F497D", margin: 0 },
  metricLabel: { fontSize: 12, color: "#888", marginTop: 4 },
  metricSub:   { fontSize: 11, color: "#AAA", marginTop: 2 },
  grid2: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    marginBottom: 16,
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "20px 24px",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    border: "0.5px solid #E0E8F0",
  },
  cardTitle: {
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
  row: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 0",
    borderBottom: "0.5px solid #F0F4F8",
  },
  rowLast: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 0",
  },
  rowTitle: { fontSize: 13, fontWeight: 500, color: "#333" },
  rowSub:   { fontSize: 12, color: "#888", marginTop: 2 },
  badge: (color) => ({
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    color: "#fff",
    background: color,
    whiteSpace: "nowrap",
  }),
  emptyState: {
    textAlign: "center",
    padding: "24px",
    color: "#AAA",
    fontSize: 13,
  },
  alertRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
    padding: "10px 0",
    borderBottom: "0.5px solid #F0F4F8",
  },
  alertIcon: (type) => ({
    width: 32, height: 32,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 14,
    flexShrink: 0,
    background: type === 'expired' || type === 'out_of_stock' ? "#FFEBEE" :
                type === 'expiring_soon' ? "#FFF3E0" : "#FFF8E1",
  }),
  refreshBtn: {
    background: "rgba(255,255,255,0.15)",
    border: "1px solid rgba(255,255,255,0.3)",
    color: "#fff",
    padding: "8px 16px",
    borderRadius: 8,
    fontSize: 13,
    cursor: "pointer",
  },
};

function MetricCard({ num, label, sub, color, loading }) {
  return (
    <div style={S.metricCard(color)}>
      <div style={S.metricNum}>{loading ? "—" : num}</div>
      <div style={S.metricLabel}>{label}</div>
      {sub && <div style={S.metricSub}>{sub}</div>}
    </div>
  );
}

export default function Dashboard({ token = "" }) {
  const [bookingSummary,  setBookingSummary]  = useState(null);
  const [needsSummary,    setNeedsSummary]    = useState(null);
  const [stockSummary,    setStockSummary]    = useState(null);
  const [procSummary,     setProcSummary]     = useState(null);
  const [pendingBookings, setPendingBookings] = useState([]);
  const [recentNeeds,     setRecentNeeds]     = useState([]);
  const [alerts,          setAlerts]          = useState([]);
  const [lowStock,        setLowStock]        = useState([]);
  const [loading,         setLoading]         = useState(true);
  const [lastRefresh,     setLastRefresh]     = useState(new Date());

  const headers = { "Authorization": `Bearer ${token}` };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [bSum, nSum, sSum, pSum, pBook, rNeeds, sAlerts, sStock] =
        await Promise.all([
          fetch(`${API_BASE}/bookings/summary/`,       { headers }).then(r => r.json()),
          fetch(`${API_BASE}/needs/summary/`,          { headers }).then(r => r.json()),
          fetch(`${API_BASE}/stock/summary/`,          { headers }).then(r => r.json()),
          fetch(`${API_BASE}/purchase-orders/summary/`,{ headers }).then(r => r.json()),
          fetch(`${API_BASE}/bookings/?status=pending&ordering=-created_at`, { headers }).then(r => r.json()),
          fetch(`${API_BASE}/needs/?status=submitted&ordering=-created_at`,  { headers }).then(r => r.json()),
          fetch(`${API_BASE}/stock-alerts/?resolved=false`,                  { headers }).then(r => r.json()),
          fetch(`${API_BASE}/stock/?low_stock=true`,                         { headers }).then(r => r.json()),
        ]);

      setBookingSummary(bSum);
      setNeedsSummary(nSum);
      setStockSummary(sSum);
      setProcSummary(pSum);
      setPendingBookings(pBook.results || []);
      setRecentNeeds(rNeeds.results || []);
      setAlerts(sAlerts.results || []);
      setLowStock(Array.isArray(sStock) ? sStock : sStock.results || []);
      setLastRefresh(new Date());
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (token) fetchAll(); }, [token]);

  return (
    <div style={S.page}>
      <div style={S.container}>

        {/* Welcome bar */}
        <div style={S.welcome}>
          <div>
            <p style={S.welcomeTitle}>🏛 Future University LIMS — Dashboard</p>
            <p style={S.welcomeSub}>
              APU Building · 4 Labs · Last updated: {lastRefresh.toLocaleTimeString("id-ID")}
            </p>
          </div>
          <button style={S.refreshBtn} onClick={fetchAll}>
            ↻ Refresh
          </button>
        </div>

        {/* Metric cards */}
        <div style={S.metricGrid}>
          <MetricCard
            num={bookingSummary?.pending || 0}
            label="Bookings pending"
            sub={`${bookingSummary?.today || 0} sessions today`}
            color="#F39C12"
            loading={loading}
          />
          <MetricCard
            num={needsSummary?.submitted || 0}
            label="Needs requests"
            sub={`${needsSummary?.total || 0} total submitted`}
            color="#2980B9"
            loading={loading}
          />
          <MetricCard
            num={stockSummary?.total_items || 0}
            label="Stock items"
            sub={`${stockSummary?.low_stock_count || 0} low stock`}
            color="#27AE60"
            loading={loading}
          />
          <MetricCard
            num={stockSummary?.unresolved_alerts || 0}
            label="Active alerts"
            sub={`${stockSummary?.expired_count || 0} expired items`}
            color="#E74C3C"
            loading={loading}
          />
        </div>

        {/* Row 1 — Pending bookings + Needs requests */}
        <div style={S.grid2}>

          {/* Pending bookings */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>📅</span> Pending Bookings
              <span style={{
                marginLeft: "auto", fontSize: 11,
                background: "#FFF3CD", color: "#856404",
                padding: "2px 8px", borderRadius: 20,
              }}>
                {pendingBookings.length} waiting
              </span>
            </div>
            {loading ? (
              <div style={S.emptyState}>Loading...</div>
            ) : pendingBookings.length === 0 ? (
              <div style={S.emptyState}>No pending bookings ✓</div>
            ) : (
              pendingBookings.slice(0, 5).map((b, i) => (
                <div key={b.id} style={
                  i === Math.min(pendingBookings.length, 5) - 1 ? S.rowLast : S.row
                }>
                  <div>
                    <div style={S.rowTitle}>
                      {b.lab_room?.name || b.equipment?.name || "—"}
                    </div>
                    <div style={S.rowSub}>
                      {b.booking_code} · {b.booked_by?.full_name}
                      <br/>
                      {new Date(b.start_time).toLocaleString("id-ID")}
                    </div>
                  </div>
                  <span style={S.badge(STATUS_COLORS.pending)}>Pending</span>
                </div>
              ))
            )}
          </div>

          {/* Needs requests */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>🧪</span> Needs Requests
              <span style={{
                marginLeft: "auto", fontSize: 11,
                background: "#E3F2FD", color: "#0C447C",
                padding: "2px 8px", borderRadius: 20,
              }}>
                {recentNeeds.length} submitted
              </span>
            </div>
            {loading ? (
              <div style={S.emptyState}>Loading...</div>
            ) : recentNeeds.length === 0 ? (
              <div style={S.emptyState}>No pending requests ✓</div>
            ) : (
              recentNeeds.slice(0, 5).map((n, i) => (
                <div key={n.id} style={
                  i === Math.min(recentNeeds.length, 5) - 1 ? S.rowLast : S.row
                }>
                  <div>
                    <div style={S.rowTitle}>
                      {n.catalogue_item?.common_name || "—"}
                    </div>
                    <div style={S.rowSub}>
                      {n.request_code} · {n.requested_by?.full_name}
                      <br/>
                      Qty: {n.quantity_requested} {n.unit} · {n.urgency}
                    </div>
                  </div>
                  <span style={S.badge(STATUS_COLORS.submitted)}>Submitted</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Row 2 — Stock alerts + Low stock */}
        <div style={S.grid2}>

          {/* Stock alerts */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>⚠️</span> Stock Alerts
              <span style={{
                marginLeft: "auto", fontSize: 11,
                background: "#FFEBEE", color: "#C62828",
                padding: "2px 8px", borderRadius: 20,
              }}>
                {alerts.length} active
              </span>
            </div>
            {loading ? (
              <div style={S.emptyState}>Loading...</div>
            ) : alerts.length === 0 ? (
              <div style={S.emptyState}>No active alerts ✓</div>
            ) : (
              alerts.slice(0, 5).map((a, i) => (
                <div key={a.id} style={S.alertRow}>
                  <div style={S.alertIcon(a.alert_type)}>
                    {a.alert_type === 'expired'      ? '☠' :
                     a.alert_type === 'out_of_stock' ? '📭' :
                     a.alert_type === 'expiring_soon'? '⏳' : '⚡'}
                  </div>
                  <div>
                    <div style={S.rowTitle}>
                      {a.stock_item?.catalogue_item?.common_name || "—"}
                    </div>
                    <div style={S.rowSub}>{a.message}</div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Low stock items */}
          <div style={S.card}>
            <div style={S.cardTitle}>
              <span>📦</span> Low Stock Items
              <span style={{
                marginLeft: "auto", fontSize: 11,
                background: "#FFF3E0", color: "#E65100",
                padding: "2px 8px", borderRadius: 20,
              }}>
                {stockSummary?.low_stock_count || 0} items
              </span>
            </div>
            {loading ? (
              <div style={S.emptyState}>Loading...</div>
            ) : lowStock.length === 0 ? (
              <div style={S.emptyState}>All stock levels OK ✓</div>
            ) : (
              lowStock.slice(0, 5).map((s, i) => (
                <div key={s.id} style={
                  i === Math.min(lowStock.length, 5) - 1 ? S.rowLast : S.row
                }>
                  <div>
                    <div style={S.rowTitle}>
                      {s.catalogue_item?.common_name || "—"}
                    </div>
                    <div style={S.rowSub}>
                      {s.lab_room?.room_code} · {s.quantity} {s.unit} remaining
                      <br/>
                      Min: {s.min_stock} {s.unit}
                    </div>
                  </div>
                  <span style={S.badge(STATUS_COLORS.low_stock)}>Low</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Row 3 — Procurement summary */}
        <div style={S.card}>
          <div style={S.cardTitle}><span>🛒</span> Procurement Overview</div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(6, 1fr)",
            gap: 12,
          }}>
            {[
              { label: "Draft",     value: procSummary?.draft     || 0, color: "#888" },
              { label: "Submitted", value: procSummary?.submitted  || 0, color: "#2980B9" },
              { label: "Approved",  value: procSummary?.approved   || 0, color: "#27AE60" },
              { label: "Ordered",   value: procSummary?.ordered    || 0, color: "#8E44AD" },
              { label: "Received",  value: procSummary?.received   || 0, color: "#1ABC9C" },
              { label: "Total POs", value: procSummary?.total      || 0, color: "#1F497D" },
            ].map(item => (
              <div key={item.label} style={{
                textAlign: "center",
                padding: "12px 8px",
                background: "#F8FAFB",
                borderRadius: 8,
                border: "0.5px solid #E0E8F0",
              }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: item.color }}>
                  {loading ? "—" : item.value}
                </div>
                <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        <p style={{ textAlign: "center", fontSize: 11, color: "#CCC", marginTop: 16 }}>
          Future University LIMS · APU Building · github.com/Lvmnd/lab-sys
        </p>

      </div>
    </div>
  );
}
