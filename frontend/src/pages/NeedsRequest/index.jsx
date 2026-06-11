/**
 * NeedsRequest/index.jsx — Needs Request Form
 * Future University LIMS
 * The main form for users to submit lab item requests
 */

import { useState, useEffect, useCallback } from "react";

const API_BASE = "http://localhost:8000/api";

// ── CONSTANTS ─────────────────────────────────────────────
const FLOORS = [
  { value: "APU", label: "APU Building" },
  { value: "1",   label: "Floor 1 — Teaching Lab (New Building)" },
  { value: "2",   label: "Floor 2 — Teaching Lab (New Building)" },
  { value: "3",   label: "Floor 3 — Teaching Lab (New Building)" },
  { value: "4",   label: "Floor 4 — Research Lab (New Building)" },
  { value: "5",   label: "Floor 5 — Office (New Building)" },
];

const PROGRAMS = [
  { value: "Biomedical",  label: "Biomedical" },
  { value: "Biotech",     label: "Biotechnology" },
  { value: "Agritech",    label: "Agricultural Technology" },
  { value: "Food",        label: "Food Technology" },
  { value: "Pharmacy",    label: "Pharmacy" },
  { value: "Medicine",    label: "Medicine" },
  { value: "General",     label: "General / Cross-program" },
];

const URGENCY = [
  { value: "low",    label: "Low — within 30 days",  color: "#27AE60" },
  { value: "medium", label: "Medium — within 14 days", color: "#F39C12" },
  { value: "high",   label: "High — within 7 days",  color: "#E67E22" },
  { value: "urgent", label: "Urgent — within 3 days", color: "#E74C3C" },
];

const GHS_COLORS = {
  Flammable:      "#E74C3C",
  Corrosive:      "#8E44AD",
  Toxic:          "#2C3E50",
  Irritant:       "#F39C12",
  Oxidizing:      "#E67E22",
  "Health Hazard":"#C0392B",
  Environmental:  "#27AE60",
  "Compressed Gas":"#2980B9",
  Explosive:      "#F1C40F",
};

// ── STYLES ────────────────────────────────────────────────
const S = {
  page: {
    minHeight: "100vh",
    background: "#F4F6F9",
    fontFamily: "'Segoe UI', Arial, sans-serif",
    padding: "24px 16px",
  },
  container: {
    maxWidth: 860,
    margin: "0 auto",
  },
  header: {
    background: "#1F497D",
    borderRadius: 12,
    padding: "20px 28px",
    marginBottom: 24,
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  headerIcon: { fontSize: 32 },
  headerTitle: {
    color: "#fff",
    fontSize: 22,
    fontWeight: 700,
    margin: 0,
  },
  headerSub: {
    color: "#BDD0E8",
    fontSize: 13,
    margin: "4px 0 0",
  },
  card: {
    background: "#fff",
    borderRadius: 12,
    padding: "24px 28px",
    marginBottom: 20,
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
  row: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    marginBottom: 16,
  },
  row3: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
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
    transition: "border 0.2s",
  },
  textarea: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    outline: "none",
    background: "#FAFCFF",
    resize: "vertical",
    minHeight: 80,
    fontFamily: "inherit",
  },
  select: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    background: "#FAFCFF",
    cursor: "pointer",
  },
  searchWrap: { position: "relative" },
  searchInput: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    width: "100%",
    outline: "none",
    background: "#FAFCFF",
    boxSizing: "border-box",
  },
  dropdown: {
    position: "absolute",
    top: "calc(100% + 4px)",
    left: 0, right: 0,
    background: "#fff",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
    zIndex: 100,
    maxHeight: 280,
    overflowY: "auto",
  },
  dropdownItem: {
    padding: "10px 14px",
    cursor: "pointer",
    borderBottom: "0.5px solid #F0F4F8",
    transition: "background 0.15s",
  },
  dropdownItemName: { fontSize: 14, fontWeight: 500, color: "#1F497D" },
  dropdownItemSub: { fontSize: 11, color: "#888", marginTop: 2 },
  selectedItem: {
    background: "#EBF3FC",
    border: "1px solid #A8C8E8",
    borderRadius: 8,
    padding: "12px 14px",
    marginTop: 8,
  },
  selectedName: { fontSize: 14, fontWeight: 600, color: "#1F497D" },
  selectedMeta: { fontSize: 12, color: "#666", marginTop: 4 },
  ghsBadge: {
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    color: "#fff",
    margin: "2px 3px 2px 0",
  },
  storageBadge: {
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    background: "#FFF3CD",
    color: "#856404",
    border: "1px solid #FFECB5",
    marginTop: 4,
  },
  urgencyRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 8,
    marginBottom: 16,
  },
  urgencyBtn: (selected, color) => ({
    padding: "10px 8px",
    borderRadius: 8,
    border: `2px solid ${selected ? color : "#D0DCE8"}`,
    background: selected ? color + "18" : "#FAFCFF",
    cursor: "pointer",
    textAlign: "center",
    transition: "all 0.2s",
  }),
  urgencyLabel: (selected, color) => ({
    fontSize: 12,
    fontWeight: selected ? 700 : 400,
    color: selected ? color : "#666",
  }),
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
    letterSpacing: 0.5,
    transition: "background 0.2s",
  },
  successBox: {
    background: "#E8F5E9",
    border: "1px solid #A5D6A7",
    borderRadius: 12,
    padding: "28px",
    textAlign: "center",
  },
  successIcon: { fontSize: 48, marginBottom: 12 },
  successTitle: { fontSize: 20, fontWeight: 700, color: "#2E7D32", marginBottom: 8 },
  successCode: {
    display: "inline-block",
    background: "#fff",
    border: "1px solid #A5D6A7",
    borderRadius: 8,
    padding: "8px 20px",
    fontSize: 22,
    fontWeight: 700,
    color: "#1F497D",
    letterSpacing: 2,
    margin: "8px 0 16px",
  },
  errorBox: {
    background: "#FFEBEE",
    border: "1px solid #FFCDD2",
    borderRadius: 8,
    padding: "12px 16px",
    color: "#C62828",
    fontSize: 13,
    marginBottom: 16,
  },
  hint: { fontSize: 11, color: "#999", marginTop: 2 },
};

// ── COMPONENTS ────────────────────────────────────────────
function GHSBadge({ codes }) {
  if (!codes) return null;
  return (
    <div style={{ marginTop: 4 }}>
      {codes.split(",").map(c => {
        const label = c.trim();
        const color = Object.keys(GHS_COLORS).find(k =>
          label.toLowerCase().includes(k.toLowerCase())
        );
        return (
          <span
            key={label}
            style={{ ...S.ghsBadge, background: color ? GHS_COLORS[color] : "#888" }}
          >
            {label}
          </span>
        );
      })}
    </div>
  );
}

function ItemCard({ item }) {
  return (
    <div style={S.selectedItem}>
      <div style={S.selectedName}>{item.common_name}</div>
      <div style={S.selectedMeta}>
        {item.iupac_name && <span>IUPAC: {item.iupac_name} &nbsp;|&nbsp; </span>}
        {item.cas_number && <span>CAS: {item.cas_number} &nbsp;|&nbsp; </span>}
        <span>Unit: {item.unit}</span>
      </div>
      {item.ghs_pictograms && <GHSBadge codes={item.ghs_pictograms} />}
      {item.storage_condition && (
        <span style={S.storageBadge}>🗄 Storage: {item.storage_condition}</span>
      )}
    </div>
  );
}

// ── MAIN FORM ─────────────────────────────────────────────
export default function NeedsRequestForm({ token = "" }) {
  const [query,       setQuery]       = useState("");
  const [results,     setResults]     = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDrop,    setShowDrop]    = useState(false);
  const [loading,     setLoading]     = useState(false);
  const [submitting,  setSubmitting]  = useState(false);
  const [submitted,   setSubmitted]   = useState(null);
  const [error,       setError]       = useState("");

  const [form, setForm] = useState({
    quantity: "",
    reason: "",
    floor: "",
    lab_room: "",
    study_program: "",
    urgency: "medium",
    date_needed: "",
  });

  // Live search with debounce
  useEffect(() => {
    if (query.length < 2) { setResults([]); return; }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/catalogue/search/?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        setResults(data);
        setShowDrop(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const selectItem = (item) => {
    setSelectedItem(item);
    setQuery(item.common_name);
    setShowDrop(false);
    setResults([]);
  };

  const setField = (key, value) => setForm(f => ({ ...f, [key]: value }));

  // Min date = today
  const today = new Date().toISOString().split("T")[0];

  const validate = () => {
    if (!selectedItem)       return "Please select an item from the catalogue.";
    if (!form.quantity || Number(form.quantity) <= 0)
                             return "Please enter a valid quantity.";
    if (!form.reason.trim()) return "Please explain why this item is needed.";
    if (!form.floor)         return "Please select a floor.";
    if (!form.study_program) return "Please select a study program.";
    if (!form.date_needed)   return "Please select a date needed.";
    if (form.date_needed < today) return "Date needed cannot be in the past.";
    return null;
  };

  const handleSubmit = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    setError("");
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/needs/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          catalogue_item_id:  selectedItem.id,
          quantity_requested: Number(form.quantity),
          unit:               selectedItem.unit,
          reason:             form.reason,
          floor:              form.floor,
          lab_room:           form.lab_room,
          study_program:      form.study_program,
          urgency:            form.urgency,
          date_needed:        form.date_needed,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(JSON.stringify(data));
        return;
      }
      const data = await res.json();
      setSubmitted(data);
    } catch (e) {
      setError("Network error — please check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setSubmitted(null); setSelectedItem(null);
    setQuery(""); setForm({
      quantity: "", reason: "", floor: "", lab_room: "",
      study_program: "", urgency: "medium", date_needed: "",
    });
  };

  // ── SUCCESS SCREEN ──────────────────────────────────────
  if (submitted) {
    return (
      <div style={S.page}>
        <div style={S.container}>
          <div style={S.successBox}>
            <div style={S.successIcon}>✅</div>
            <div style={S.successTitle}>Request Submitted Successfully!</div>
            <div style={{ fontSize: 13, color: "#555", marginBottom: 8 }}>
              Your request code is:
            </div>
            <div style={S.successCode}>{submitted.request_code}</div>
            <div style={{ fontSize: 13, color: "#555", marginBottom: 20 }}>
              Item: <strong>{submitted.catalogue_item?.common_name}</strong>
              &nbsp;·&nbsp;
              Qty: <strong>{submitted.quantity_requested} {submitted.unit}</strong>
              &nbsp;·&nbsp;
              Status: <strong>Submitted</strong>
            </div>
            <div style={{ fontSize: 12, color: "#777", marginBottom: 20 }}>
              You will be notified when your request is reviewed by the lab admin.
              Keep your request code for tracking.
            </div>
            <button style={S.submitBtn} onClick={reset}>
              Submit Another Request
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── MAIN FORM ───────────────────────────────────────────
  return (
    <div style={S.page}>
      <div style={S.container}>

        {/* Header */}
        <div style={S.header}>
          <span style={S.headerIcon}>🧪</span>
          <div>
            <h1 style={S.headerTitle}>Lab Item Request Form</h1>
            <p style={S.headerSub}>
              Future University — Integrated Laboratory &nbsp;|&nbsp;
              Submit your needs and we will procure what is required
            </p>
          </div>
        </div>

        {error && <div style={S.errorBox}>⚠ {error}</div>}

        {/* Section 1: Item Search */}
        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>🔬</span> 1. Select Item from Catalogue
          </div>
          <div style={S.field}>
            <label style={S.label}>SEARCH ITEM *</label>
            <div style={S.searchWrap}>
              <input
                style={S.searchInput}
                placeholder="Type chemical name, CAS number, or category... (min 2 characters)"
                value={query}
                onChange={e => { setQuery(e.target.value); setSelectedItem(null); }}
                onFocus={() => results.length > 0 && setShowDrop(true)}
              />
              {loading && (
                <span style={{ position: "absolute", right: 12, top: 11, fontSize: 12, color: "#999" }}>
                  Searching...
                </span>
              )}
              {showDrop && results.length > 0 && (
                <div style={S.dropdown}>
                  {results.map(item => (
                    <div
                      key={item.id}
                      style={S.dropdownItem}
                      onMouseDown={() => selectItem(item)}
                      onMouseEnter={e => e.currentTarget.style.background = "#F0F7FF"}
                      onMouseLeave={e => e.currentTarget.style.background = ""}
                    >
                      <div style={S.dropdownItemName}>{item.common_name}</div>
                      <div style={S.dropdownItemSub}>
                        {item.cas_number && `CAS: ${item.cas_number} · `}
                        {item.category} · Unit: {item.unit}
                        {item.is_hazardous && " · ⚠ Hazardous"}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {showDrop && query.length >= 2 && results.length === 0 && !loading && (
                <div style={S.dropdown}>
                  <div style={{ padding: "12px 14px", fontSize: 13, color: "#888" }}>
                    No items found for "{query}". Contact admin to add new catalogue items.
                  </div>
                </div>
              )}
            </div>
            <span style={S.hint}>
              Search by common name (e.g. "Acetic Acid"), CAS number (e.g. "64-19-7"), or category
            </span>
          </div>
          {selectedItem && <ItemCard item={selectedItem} />}
        </div>

        {/* Section 2: Quantity */}
        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>📦</span> 2. Quantity & Details
          </div>
          <div style={S.row}>
            <div style={S.field}>
              <label style={S.label}>QUANTITY NEEDED *</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                style={S.input}
                placeholder="e.g. 500"
                value={form.quantity}
                onChange={e => setField("quantity", e.target.value)}
              />
            </div>
            <div style={S.field}>
              <label style={S.label}>UNIT</label>
              <input
                style={{ ...S.input, background: "#F0F4F8", color: "#888" }}
                value={selectedItem ? selectedItem.unit : "— select item first —"}
                readOnly
              />
            </div>
          </div>
          <div style={S.field}>
            <label style={S.label}>REASON / PURPOSE *</label>
            <textarea
              style={S.textarea}
              placeholder="Explain why this item is needed and what experiment or activity it will be used for..."
              value={form.reason}
              onChange={e => setField("reason", e.target.value)}
            />
          </div>
        </div>

        {/* Section 3: Location */}
        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>🏢</span> 3. Location & Program
          </div>
          <div style={S.row}>
            <div style={S.field}>
              <label style={S.label}>FLOOR *</label>
              <select
                style={S.select}
                value={form.floor}
                onChange={e => setField("floor", e.target.value)}
              >
                <option value="">Select floor...</option>
                {FLOORS.map(f => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <div style={S.field}>
              <label style={S.label}>LAB ROOM</label>
              <input
                style={S.input}
                placeholder="e.g. Lab Microbiology 1A"
                value={form.lab_room}
                onChange={e => setField("lab_room", e.target.value)}
              />
            </div>
          </div>
          <div style={S.field}>
            <label style={S.label}>STUDY PROGRAM *</label>
            <select
              style={S.select}
              value={form.study_program}
              onChange={e => setField("study_program", e.target.value)}
            >
              <option value="">Select study program...</option>
              {PROGRAMS.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Section 4: Urgency & Date */}
        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>📅</span> 4. Urgency & Timeline
          </div>
          <div style={S.field}>
            <label style={S.label}>URGENCY LEVEL *</label>
            <div style={S.urgencyRow}>
              {URGENCY.map(u => (
                <div
                  key={u.value}
                  style={S.urgencyBtn(form.urgency === u.value, u.color)}
                  onClick={() => setField("urgency", u.value)}
                >
                  <div style={S.urgencyLabel(form.urgency === u.value, u.color)}>
                    {u.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div style={S.field}>
            <label style={S.label}>DATE NEEDED BY *</label>
            <input
              type="date"
              style={S.input}
              min={today}
              value={form.date_needed}
              onChange={e => setField("date_needed", e.target.value)}
            />
            <span style={S.hint}>
              The date you need this item to be available in the lab
            </span>
          </div>
        </div>

        {/* Submit */}
        <button
          style={{
            ...S.submitBtn,
            opacity: submitting ? 0.7 : 1,
            cursor: submitting ? "not-allowed" : "pointer",
          }}
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? "Submitting..." : "Submit Request →"}
        </button>

        <p style={{ textAlign: "center", fontSize: 12, color: "#999", marginTop: 12 }}>
          Future University LIMS · Integrated International Laboratory · Semarang
        </p>

      </div>
    </div>
  );
}