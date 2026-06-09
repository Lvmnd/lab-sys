import { useState } from "react";

const API_BASE = "http://localhost:8000/api";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      setError("Please enter username and password.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login/`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        setError("Invalid username or password.");
        return;
      }
      const data = await res.json();
      localStorage.setItem("lims_token",    data.access);
      localStorage.setItem("lims_refresh",  data.refresh);
      localStorage.setItem("lims_username", username);
      onLogin(username, data.access);
    } catch {
      setError("Cannot connect to server. Make sure Django is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#F4F6F9",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Segoe UI', Arial, sans-serif",
      padding: 16,
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 16,
        padding: "40px 36px",
        width: "100%",
        maxWidth: 400,
        boxShadow: "0 4px 24px rgba(0,0,0,0.10)",
        border: "0.5px solid #E0E8F0",
      }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🏛</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#1F497D", margin: "0 0 6px" }}>
            Future University
          </h1>
          <p style={{ fontSize: 14, color: "#888", margin: 0 }}>
            Laboratory Information Management System
          </p>
          <p style={{ fontSize: 12, color: "#AAA", margin: "4px 0 0" }}>
            APU Building · 4 Labs active
          </p>
        </div>

        {error && (
          <div style={{
            background: "#FFEBEE",
            border: "1px solid #FFCDD2",
            borderRadius: 8,
            padding: "10px 14px",
            color: "#C62828",
            fontSize: 13,
            marginBottom: 16,
          }}>
            ⚠ {error}
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#555" }}>USERNAME</label>
            <input
              style={{
                padding: "11px 14px",
                border: "1px solid #D0DCE8",
                borderRadius: 8,
                fontSize: 14,
                outline: "none",
                background: "#FAFCFF",
              }}
              placeholder="Enter your username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleLogin()}
              autoFocus
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#555" }}>PASSWORD</label>
            <input
              type="password"
              style={{
                padding: "11px 14px",
                border: "1px solid #D0DCE8",
                borderRadius: 8,
                fontSize: 14,
                outline: "none",
                background: "#FAFCFF",
              }}
              placeholder="Enter your password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleLogin()}
            />
          </div>

          <button
            onClick={handleLogin}
            disabled={loading}
            style={{
              padding: "13px",
              background: loading ? "#7FA8C9" : "#1F497D",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 15,
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
              marginTop: 4,
              transition: "background 0.2s",
            }}
          >
            {loading ? "Signing in..." : "Sign In →"}
          </button>
        </div>

        <p style={{ textAlign: "center", fontSize: 11, color: "#BBB", marginTop: 24 }}>
          Contact your Lab Admin if you need access
        </p>
      </div>
    </div>
  );
}
