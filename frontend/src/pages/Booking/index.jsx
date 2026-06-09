/**
 * Booking/index.jsx — Lab Room & Equipment Booking Form
 * Future University LIMS
 */

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

const FLOORS = [
  { value: "",    label: "All Floors" },
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
  { value: "General",     label: "General" },
];

const PURPOSES = [
  { value: "class",       label: "Practical Class" },
  { value: "research",    label: "Research" },
  { value: "analysis",    label: "Sample Analysis" },
  { value: "training",    label: "Equipment Training" },
  { value: "other",       label: "Other" },
];

const STATUS_COLORS = {
  available:   "#27AE60",
  maintenance: "#E67E22",
  reserved:    "#E74C3C",
  inactive:    "#95A5A6",
};

const BOOKING_STATUS_COLORS = {
  pending:   "#F39C12",
  approved:  "#27AE60",
  rejected:  "#E74C3C",
  cancelled: "#95A5A6",
  ongoing:   "#2980B9",
  completed: "#7F8C8D",
};

// ── STYLES ────────────────────────────────────────────────
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
  tabs: {
    display: "flex",
    gap: 4,
    marginBottom: 20,
    background: "#fff",
    padding: 6,
    borderRadius: 10,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  tab: (active) => ({
    flex: 1,
    padding: "10px 16px",
    borderRadius: 8,
    border: "none",
    background: active ? "#1F497D" : "transparent",
    color: active ? "#fff" : "#666",
    fontWeight: active ? 700 : 400,
    fontSize: 14,
    cursor: "pointer",
    transition: "all 0.2s",
  }),
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
  filterRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: 12,
    marginBottom: 16,
  },
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
  textarea: {
    padding: "10px 12px",
    border: "1px solid #D0DCE8",
    borderRadius: 8,
    fontSize: 14,
    background: "#FAFCFF",
    resize: "vertical",
    minHeight: 72,
    fontFamily: "inherit",
  },
  roomGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
    gap: 12,
    marginBottom: 16,
  },
  roomCard: (selected, bookable) => ({
    border: `2px solid ${selected ? "#1F497D" : bookable ? "#D0DCE8" : "#FFCDD2"}`,
    borderRadius: 10,
    padding: "14px 16px",
    cursor: bookable ? "pointer" : "not-allowed",
    background: selected ? "#EBF3FC" : bookable ? "#fff" : "#FFF5F5",
    transition: "all 0.2s",
    opacity: bookable ? 1 : 0.7,
  }),
  roomCode: { fontSize: 11, fontWeight: 700, color: "#888", letterSpacing: 1 },
  roomName: { fontSize: 14, fontWeight: 600, color: "#1F497D", margin: "4px 0 2px" },
  roomMeta: { fontSize: 12, color: "#666" },
  statusDot: (color) => ({
    display: "inline-block",
    width: 8, height: 8,
    borderRadius: "50%",
    background: color,
    marginRight: 5,
  }),
  equipGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
    gap: 12,
    marginBottom: 16,
  },
  equipCard: (selected, bookable) => ({
    border: `2px solid ${selected ? "#1F497D" : bookable ? "#D0DCE8" : "#FFCDD2"}`,
    borderRadius: 10,
    padding: "14px 16px",
    cursor: bookable ? "pointer" : "not-allowed",
    background: selected ? "#EBF3FC" : "#fff",
    transition: "all 0.2s",
    opacity: bookable ? 1 : 0.7,
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
    transition: "background 0.2s",
  },
  successBox: {
    background: "#E8F5E9",
    border: "1px solid #A5D6A7",
    borderRadius: 12,
    padding: "28px",
    textAlign: "center",
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
  bookingRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 0",
    borderBottom: "0.5px solid #F0F4F8",
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
  emptyState: {
    textAlign: "center",
    padding: "40px 20px",
    color: "#999",
    fontSize: 14,
  },
};

// ── MAIN COMPONENT ────────────────────────────────────────
export default function BookingPage({ token = "" }) {
  const [activeTab, setActiveTab] = useState("book");

  return (
    <div style={S.page}>
      <div style={S.container}>
        <div style={S.header}>
          <span style={{ fontSize: 32 }}>📅</span>
          <div>
            <h1 style={S.headerTitle}>Lab Booking System</h1>
            <p style={S.headerSub}>
              Future University — Book lab rooms and equipment across all floors
            </p>
          </div>
        </div>

        <div style={S.tabs}>
          {[
            { key: "book",     label: "📝 New Booking" },
            { key: "rooms",    label: "🏢 Browse Rooms" },
            { key: "mybookings", label: "📋 My Bookings" },
          ].map(t => (
            <button
              key={t.key}
              style={S.tab(activeTab === t.key)}
              onClick={() => setActiveTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === "book"       && <NewBookingForm token={token} />}
        {activeTab === "rooms"      && <RoomBrowser />}
        {activeTab === "mybookings" && <MyBookings token={token} />}
      </div>
    </div>
  );
}

// ── NEW BOOKING FORM ──────────────────────────────────────
function NewBookingForm({ token }) {
  const [step,          setStep]          = useState(1);
  const [bookingType,   setBookingType]   = useState("room");
  const [rooms,         setRooms]         = useState([]);
  const [equipment,     setEquipment]     = useState([]);
  const [selectedRoom,  setSelectedRoom]  = useState(null);
  const [selectedEquip, setSelectedEquip] = useState(null);
  const [filterFloor,   setFilterFloor]   = useState("");
  const [loading,       setLoading]       = useState(false);
  const [submitting,    setSubmitting]    = useState(false);
  const [submitted,     setSubmitted]     = useState(null);
  const [error,         setError]         = useState("");

  const [form, setForm] = useState({
    start_time:        "",
    end_time:          "",
    purpose:           "",
    study_program:     "",
    participant_count: 1,
    notes:             "",
  });

  const setField = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const today    = new Date().toISOString().slice(0, 16);

  // Load rooms
  useEffect(() => {
    if (bookingType !== "room") return;
    setLoading(true);
    const params = new URLSearchParams({ available_only: "true" });
    if (filterFloor) params.set("floor", filterFloor);
    const url = `${API_BASE}/rooms/?${params}`;
    console.log("Fetching rooms from:", url);
    fetch(url)
      .then(r => r.json())
      .then(d => setRooms(d.results || (Array.isArray(d) ? d : [])))
      .catch(() => setRooms([]))
      .finally(() => setLoading(false));
  }, [bookingType, filterFloor]);

  // Load equipment
  useEffect(() => {
    if (bookingType !== "equipment") return;
    setLoading(true);
    const params = new URLSearchParams({ available_only: "true" });
    if (filterFloor) params.set("floor", filterFloor);
    fetch(`${API_BASE}/equipment/?${params}`)
      .then(r => r.json())
      .then(d => setEquipment(d.results || (Array.isArray(d) ? d : [])))
      .catch(() => setEquipment([]))
      .finally(() => setLoading(false));
  }, [bookingType, filterFloor]);

  const validate = () => {
    if (bookingType === "room"      && !selectedRoom)  return "Please select a room.";
    if (bookingType === "equipment" && !selectedEquip) return "Please select equipment.";
    if (!form.start_time)  return "Please set a start time.";
    if (!form.end_time)    return "Please set an end time.";
    if (form.end_time <= form.start_time) return "End time must be after start time.";
    if (!form.purpose)     return "Please select a purpose.";
    if (!form.study_program) return "Please select a study program.";
    return null;
  };

  const handleSubmit = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    setError("");
    setSubmitting(true);
    try {
      const body = {
        start_time:        form.start_time + ":00",
        end_time:          form.end_time   + ":00",
        purpose:           form.purpose,
        study_program:     form.study_program,
        participant_count: Number(form.participant_count),
        notes:             form.notes,
      };
      if (bookingType === "room")      body.lab_room_id  = selectedRoom.id;
      if (bookingType === "equipment") body.equipment_id = selectedEquip.id;

      const res = await fetch(`${API_BASE}/bookings/`, {
        method:  "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body:    JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json();
        const msg  = typeof data === "object"
          ? Object.values(data).flat().join(" ")
          : JSON.stringify(data);
        setError(msg);
        return;
      }
      setSubmitted(await res.json());
    } catch {
      setError("Network error — please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setSubmitted(null); setSelectedRoom(null); setSelectedEquip(null);
    setStep(1); setError("");
    setForm({ start_time:"", end_time:"", purpose:"",
              study_program:"", participant_count:1, notes:"" });
  };

  if (submitted) {
    return (
      <div style={S.successBox}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
        <div style={{ fontSize: 20, fontWeight: 700, color: "#2E7D32", marginBottom: 8 }}>
          Booking Submitted!
        </div>
        <div style={{
          display: "inline-block", background: "#fff",
          border: "1px solid #A5D6A7", borderRadius: 8,
          padding: "8px 20px", fontSize: 22, fontWeight: 700,
          color: "#1F497D", letterSpacing: 2, margin: "8px 0 12px",
        }}>
          {submitted.booking_code}
        </div>
        <div style={{ fontSize: 13, color: "#555", marginBottom: 20 }}>
          {submitted.lab_room?.name || submitted.equipment?.name}
          &nbsp;·&nbsp;
          {new Date(submitted.start_time).toLocaleString("id-ID")}
          &nbsp;→&nbsp;
          {new Date(submitted.end_time).toLocaleTimeString("id-ID")}
          <br />
          Status: <strong>Pending Approval</strong> — you will be notified when reviewed.
        </div>
        <button style={S.submitBtn} onClick={reset}>Make Another Booking</button>
      </div>
    );
  }

  return (
    <div>
      {error && <div style={S.errorBox}>⚠ {error}</div>}

      {/* Step 1: Type + Target */}
      <div style={S.card}>
        <div style={S.sectionTitle}>
          <span>🏢</span> 1. What would you like to book?
        </div>

        {/* Booking type toggle */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {[
            { key: "room",      label: "🏛 Lab Room" },
            { key: "equipment", label: "🔬 Equipment" },
          ].map(t => (
            <button
              key={t.key}
              style={{
                flex: 1, padding: "10px",
                borderRadius: 8,
                border: `2px solid ${bookingType === t.key ? "#1F497D" : "#D0DCE8"}`,
                background: bookingType === t.key ? "#EBF3FC" : "#fff",
                color: bookingType === t.key ? "#1F497D" : "#666",
                fontWeight: bookingType === t.key ? 700 : 400,
                fontSize: 14, cursor: "pointer",
              }}
              onClick={() => { setBookingType(t.key); setSelectedRoom(null); setSelectedEquip(null); }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Floor filter */}
        <div style={{ marginBottom: 16 }}>
          <label style={S.label}>FILTER BY FLOOR</label>
          <select
            style={{ ...S.select, marginTop: 6 }}
            value={filterFloor}
            onChange={e => setFilterFloor(e.target.value)}
          >
            {FLOORS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>

        {/* Room cards */}
        {bookingType === "room" && (
          loading ? (
            <div style={S.emptyState}>Loading rooms...</div>
          ) : rooms.length === 0 ? (
            <div style={S.emptyState}>
              No rooms found. Add rooms via the admin panel first.
            </div>
          ) : (
            <div style={S.roomGrid}>
              {rooms.map(room => (
                <div
                  key={room.id}
                  style={S.roomCard(
                    selectedRoom?.id === room.id,
                    room.is_bookable
                  )}
                  onClick={() => room.is_bookable && setSelectedRoom(room)}
                >
                  <div style={S.roomCode}>{room.room_code}</div>
                  <div style={S.roomName}>{room.name}</div>
                  <div style={S.roomMeta}>
                    {room.floor_display} · Cap: {room.capacity}
                  </div>
                  <div style={{ ...S.roomMeta, marginTop: 4 }}>
                    <span style={S.statusDot(STATUS_COLORS[room.status] || "#888")} />
                    {room.status}
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Equipment cards */}
        {bookingType === "equipment" && (
          loading ? (
            <div style={S.emptyState}>Loading equipment...</div>
          ) : equipment.length === 0 ? (
            <div style={S.emptyState}>
              No equipment found. Add equipment via the admin panel first.
            </div>
          ) : (
            <div style={S.equipGrid}>
              {equipment.map(eq => (
                <div
                  key={eq.id}
                  style={S.equipCard(
                    selectedEquip?.id === eq.id,
                    eq.is_bookable
                  )}
                  onClick={() => eq.is_bookable && setSelectedEquip(eq)}
                >
                  <div style={S.roomCode}>{eq.equipment_code}</div>
                  <div style={S.roomName}>{eq.name}</div>
                  <div style={S.roomMeta}>{eq.brand} · {eq.room_name}</div>
                  <div style={{ ...S.roomMeta, marginTop: 4 }}>
                    <span style={S.statusDot(STATUS_COLORS[eq.status] || "#888")} />
                    {eq.status}
                    {eq.requires_training && " · ⚠ Training required"}
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {(selectedRoom || selectedEquip) && (
          <div style={{
            background: "#EBF3FC", borderRadius: 8,
            padding: "10px 14px", fontSize: 13, color: "#1F497D",
          }}>
            ✓ Selected: <strong>
              {selectedRoom ? `${selectedRoom.room_code} — ${selectedRoom.name}`
                            : `${selectedEquip.equipment_code} — ${selectedEquip.name}`}
            </strong>
          </div>
        )}
      </div>

      {/* Step 2: Date & Time */}
      <div style={S.card}>
        <div style={S.sectionTitle}><span>⏰</span> 2. Date & Time</div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>START DATE & TIME *</label>
            <input
              type="datetime-local"
              style={S.input}
              min={today}
              value={form.start_time}
              onChange={e => setField("start_time", e.target.value)}
            />
          </div>
          <div style={S.field}>
            <label style={S.label}>END DATE & TIME *</label>
            <input
              type="datetime-local"
              style={S.input}
              min={form.start_time || today}
              value={form.end_time}
              onChange={e => setField("end_time", e.target.value)}
            />
          </div>
        </div>
        {form.start_time && form.end_time && form.end_time > form.start_time && (
          <div style={{ fontSize: 13, color: "#27AE60", marginTop: -8 }}>
            ✓ Duration: {(
              (new Date(form.end_time) - new Date(form.start_time)) / 3600000
            ).toFixed(1)} hours
          </div>
        )}
      </div>

      {/* Step 3: Details */}
      <div style={S.card}>
        <div style={S.sectionTitle}><span>📋</span> 3. Booking Details</div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>PURPOSE *</label>
            <select
              style={S.select}
              value={form.purpose}
              onChange={e => setField("purpose", e.target.value)}
            >
              <option value="">Select purpose...</option>
              {PURPOSES.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
          <div style={S.field}>
            <label style={S.label}>STUDY PROGRAM *</label>
            <select
              style={S.select}
              value={form.study_program}
              onChange={e => setField("study_program", e.target.value)}
            >
              <option value="">Select program...</option>
              {PROGRAMS.map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>NUMBER OF PARTICIPANTS</label>
            <input
              type="number"
              min="1"
              style={S.input}
              value={form.participant_count}
              onChange={e => setField("participant_count", e.target.value)}
            />
          </div>
          <div style={S.field}>
            <label style={S.label}>NOTES (optional)</label>
            <input
              style={S.input}
              placeholder="Any special requirements..."
              value={form.notes}
              onChange={e => setField("notes", e.target.value)}
            />
          </div>
        </div>
      </div>

      <button
        style={{ ...S.submitBtn, opacity: submitting ? 0.7 : 1 }}
        onClick={handleSubmit}
        disabled={submitting}
      >
        {submitting ? "Submitting..." : "Submit Booking Request →"}
      </button>
      <p style={{ textAlign: "center", fontSize: 12, color: "#999", marginTop: 12 }}>
        Future University LIMS · Bookings require approval from Lab Technician
      </p>
    </div>
  );
}

// ── ROOM BROWSER ──────────────────────────────────────────
function RoomBrowser() {
  const [rooms,  setRooms]  = useState([]);
  const [floor,  setFloor]  = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (floor) params.set("floor", floor);
    const url = `${API_BASE}/rooms/?${params}`;
    console.log("Fetching rooms from:", url);
    fetch(url)
      .then(r => r.json())
      .then(d => setRooms(d.results || (Array.isArray(d) ? d : [])))
      .catch(() => setRooms([]))
      .finally(() => setLoading(false));
  }, [floor]);

  return (
    <div>
      <div style={S.card}>
        <div style={S.sectionTitle}><span>🏢</span> All Lab Rooms</div>
        <div style={{ marginBottom: 16 }}>
          <select
            style={S.select}
            value={floor}
            onChange={e => setFloor(e.target.value)}
          >
            {FLOORS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>
        {loading ? (
          <div style={S.emptyState}>Loading...</div>
        ) : rooms.length === 0 ? (
          <div style={S.emptyState}>
            No rooms found. Add rooms in the admin panel at
            <br />
            <code>http://localhost:8000/admin/booking/labroom/</code>
          </div>
        ) : (
          <div style={S.roomGrid}>
            {rooms.map(room => (
              <div key={room.id} style={{
                border: "1px solid #D0DCE8",
                borderRadius: 10,
                padding: "14px 16px",
                background: "#fff",
              }}>
                <div style={S.roomCode}>{room.room_code}</div>
                <div style={S.roomName}>{room.name}</div>
                <div style={S.roomMeta}>{room.floor_display}</div>
                <div style={S.roomMeta}>{room.program_display} · Cap: {room.capacity}</div>
                <div style={{ marginTop: 6 }}>
                  <span style={S.statusDot(STATUS_COLORS[room.status] || "#888")} />
                  <span style={{ fontSize: 12, color: "#666" }}>{room.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── MY BOOKINGS ───────────────────────────────────────────
function MyBookings({ token = "" }) {
  const [bookings, setBookings] = useState([]);
  const [loading,  setLoading]  = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/bookings/my-bookings/`, {
      headers: { "Authorization": `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => setBookings(Array.isArray(d) ? d : d.results || []))
      .catch(() => setBookings([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={S.card}>
      <div style={S.sectionTitle}><span>📋</span> My Upcoming Bookings</div>
      {loading ? (
        <div style={S.emptyState}>Loading...</div>
      ) : bookings.length === 0 ? (
        <div style={S.emptyState}>
          No upcoming bookings. Make a booking using the New Booking tab!
        </div>
      ) : (
        bookings.map(b => (
          <div key={b.id} style={S.bookingRow}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "#1F497D" }}>
                {b.booking_code}
              </div>
              <div style={{ fontSize: 13, color: "#444", marginTop: 2 }}>
                {b.lab_room?.name || b.equipment?.name}
              </div>
              <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
                {new Date(b.start_time).toLocaleString("id-ID")}
                &nbsp;→&nbsp;
                {new Date(b.end_time).toLocaleTimeString("id-ID")}
                &nbsp;·&nbsp;{b.duration_hours}h
              </div>
            </div>
            <span style={S.badge(BOOKING_STATUS_COLORS[b.status] || "#888")}>
              {b.status_display}
            </span>
          </div>
        ))
      )}
    </div>
  );
}
