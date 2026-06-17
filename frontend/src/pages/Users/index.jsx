/**
 * Users/index.jsx — User Management Page
 * Future University LIMS
 * Admin only — create and manage user accounts
 */

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

const ROLES = [
  { value: "Student",       label: "Student" },
  { value: "Lecturer",      label: "Lecturer" },
  { value: "Researcher",    label: "Researcher" },
  { value: "Lab Technician",label: "Lab Technician" },
  { value: "Admin",         label: "Admin" },
];

const ROLE_COLORS = {
  "Student":        "#2980B9",
  "Lecturer":       "#8E44AD",
  "Researcher":     "#27AE60",
  "Lab Technician": "#E67E22",
  "Admin":          "#E74C3C",
};

const S = {
  page: {
    minHeight: "100vh",
    background: "#F4F6F9",
    fontFamily: "'Segoe UI', Arial, sans-serif",
    padding: "24px 16px",
  },
  container: { maxWidth: 900, margin: "0 auto" },
  header: {
    background: "#1F497D",
    borderRadius: 12,
    padding: "20px 28px",
    marginBottom: 24,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerTitle: { color: "#fff", fontSize: 20, fontWeight: 700, margin: 0 },
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
  grid2: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 },
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
  btn: (color) => ({
    padding: "10px 20px",
    background: color || "#1F497D",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  }),
  userRow: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "12px 0",
    borderBottom: "0.5px solid #F0F4F8",
  },
  avatar: (role) => ({
    width: 40, height: 40,
    borderRadius: "50%",
    background: ROLE_COLORS[role] || "#888",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontWeight: 700,
    fontSize: 15,
    flexShrink: 0,
  }),
  badge: (role) => ({
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    color: "#fff",
    background: ROLE_COLORS[role] || "#888",
  }),
  errorBox: {
    background: "#FFEBEE",
    border: "1px solid #FFCDD2",
    borderRadius: 8,
    padding: "10px 14px",
    color: "#C62828",
    fontSize: 13,
    marginBottom: 14,
  },
  successBox: {
    background: "#E8F5E9",
    border: "1px solid #A5D6A7",
    borderRadius: 8,
    padding: "10px 14px",
    color: "#2E7D32",
    fontSize: 13,
    marginBottom: 14,
  },
  emptyState: {
    textAlign: "center",
    padding: "32px",
    color: "#AAA",
    fontSize: 14,
  },
};

export default function UsersPage({ token = "" }) {
  const [users,     setUsers]     = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");
  const [success,   setSuccess]   = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    username:   "",
    first_name: "",
    last_name:  "",
    email:      "",
    password:   "",
    role:       "Student",
  });

  const setField = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const headers  = {
    "Content-Type":  "application/json",
    "Authorization": `Bearer ${token}`,
  };

  // Load users
  const loadUsers = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/auth/users/`, { headers });
      if (!r.ok) return;
      const d = await r.json();
      setUsers(Array.isArray(d) ? d : d.results || []);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (token) loadUsers(); }, [token]);

  const validate = () => {
    if (!form.username.trim())   return "Username is required.";
    if (!form.first_name.trim()) return "First name is required.";
    if (!form.email.trim())      return "Email is required.";
    if (!form.password || form.password.length < 8)
      return "Password must be at least 8 characters.";
    return null;
  };

  const handleCreate = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    setError(""); setSuccess(""); setSubmitting(true);
    try {
      const r = await fetch(`${API_BASE}/auth/users/create/`, {
        method: "POST",
        headers,
        body: JSON.stringify(form),
      });
      if (!r.ok) {
        const d = await r.json();
        setError(Object.values(d).flat().join(" "));
        return;
      }
      const d = await r.json();
      setSuccess(`User "${d.username}" created successfully as ${form.role}!`);
      setForm({ username:"", first_name:"", last_name:"", email:"", password:"", role:"Student" });
      loadUsers();
    } catch {
      setError("Network error — please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const getInitials = (user) => {
    const f = user.first_name?.[0] || "";
    const l = user.last_name?.[0]  || "";
    return (f + l).toUpperCase() || user.username[0].toUpperCase();
  };

  const getRole = (user) => {
    return user.groups?.[0]?.name || "No role";
  };

  return (
    <div style={S.page}>
      <div style={S.container}>

        {/* Header */}
        <div style={S.header}>
          <div>
            <p style={S.headerTitle}>👥 User Management</p>
            <p style={S.headerSub}>
              Future University LIMS · Create and manage user accounts
            </p>
          </div>
          <div style={{
            background: "rgba(255,255,255,0.15)",
            borderRadius: 8,
            padding: "8px 16px",
            color: "#fff",
            fontSize: 13,
          }}>
            {users.length} users total
          </div>
        </div>

        {/* Create user form */}
        <div style={S.card}>
          <div style={S.sectionTitle}><span>➕</span> Create New User</div>

          {error   && <div style={S.errorBox}>⚠ {error}</div>}
          {success && <div style={S.successBox}>✓ {success}</div>}

          <div style={S.grid2}>
            <div style={S.field}>
              <label style={S.label}>USERNAME *</label>
              <input
                style={S.input}
                placeholder="e.g. student02"
                value={form.username}
                onChange={e => setField("username", e.target.value)}
              />
            </div>
            <div style={S.field}>
              <label style={S.label}>ROLE *</label>
              <select
                style={S.select}
                value={form.role}
                onChange={e => setField("role", e.target.value)}
              >
                {ROLES.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={S.grid2}>
            <div style={S.field}>
              <label style={S.label}>FIRST NAME *</label>
              <input
                style={S.input}
                placeholder="e.g. Budi"
                value={form.first_name}
                onChange={e => setField("first_name", e.target.value)}
              />
            </div>
            <div style={S.field}>
              <label style={S.label}>LAST NAME</label>
              <input
                style={S.input}
                placeholder="e.g. Santoso"
                value={form.last_name}
                onChange={e => setField("last_name", e.target.value)}
              />
            </div>
          </div>

          <div style={S.grid2}>
            <div style={S.field}>
              <label style={S.label}>EMAIL *</label>
              <input
                type="email"
                style={S.input}
                placeholder="e.g. budi@futureuniv.ac.id"
                value={form.email}
                onChange={e => setField("email", e.target.value)}
              />
            </div>
            <div style={S.field}>
              <label style={S.label}>PASSWORD *</label>
              <input
                type="password"
                style={S.input}
                placeholder="Min 8 characters"
                value={form.password}
                onChange={e => setField("password", e.target.value)}
              />
            </div>
          </div>

          <button
            style={{ ...S.btn(), opacity: submitting ? 0.7 : 1 }}
            onClick={handleCreate}
            disabled={submitting}
          >
            {submitting ? "Creating..." : "Create User →"}
          </button>
        </div>

        {/* User list */}
        <div style={S.card}>
          <div style={S.sectionTitle}>
            <span>👤</span> All Users
            <button
              style={{ ...S.btn("#27AE60"), marginLeft: "auto", padding: "6px 14px", fontSize: 12 }}
              onClick={loadUsers}
            >
              ↻ Refresh
            </button>
          </div>

          {loading ? (
            <div style={S.emptyState}>Loading users...</div>
          ) : users.length === 0 ? (
            <div style={S.emptyState}>No users found.</div>
          ) : (
            users.map(user => (
              <div key={user.id} style={S.userRow}>
                <div style={S.avatar(getRole(user))}>
                  {getInitials(user)}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#1F497D" }}>
                    {user.first_name} {user.last_name}
                    <span style={{ fontWeight: 400, color: "#888", marginLeft: 8 }}>
                      @{user.username}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: "#888", marginTop: 2 }}>
                    {user.email}
                  </div>
                </div>
                <span style={S.badge(getRole(user))}>
                  {getRole(user)}
                </span>
                <span style={{
                  fontSize: 11,
                  color: user.is_active ? "#27AE60" : "#E74C3C",
                  fontWeight: 600,
                }}>
                  {user.is_active ? "Active" : "Inactive"}
                </span>
              </div>
            ))
          )}
        </div>

      </div>
    </div>
  );
}