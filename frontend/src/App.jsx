import { useState } from "react";
import NeedsRequestForm from "./pages/NeedsRequest/index.jsx";
import BookingPage from "./pages/Booking/index.jsx";
import LoginPage from "./pages/Login/index.jsx";
import Dashboard from "./pages/Dashboard/index.jsx";
import UsersPage from "./pages/Users/index.jsx";

const NAV = [
  { key: "dashboard", label: "📊 Dashboard",    desc: "System overview" },
  { key: "booking",   label: "📅 Lab Booking",  desc: "Book rooms & equipment" },
  { key: "needs",     label: "🧪 Request Items", desc: "Submit procurement needs" },
  { key: "users",     label: "👥 Users",         desc: "Manage user accounts" },
];

export default function App() {
  const [page,     setPage]     = useState("dashboard");
  const [token,    setToken]    = useState(localStorage.getItem("lims_token") || "");
  const [username, setUsername] = useState(localStorage.getItem("lims_username") || "");

  const handleLogin = (user, accessToken) => {
    setToken(accessToken);
    setUsername(user);
  };

  const handleLogout = () => {
    localStorage.removeItem("lims_token");
    localStorage.removeItem("lims_refresh");
    localStorage.removeItem("lims_username");
    setToken("");
    setUsername("");
  };

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div style={{ minHeight: "100vh", background: "#F4F6F9", fontFamily: "'Segoe UI', Arial, sans-serif" }}>
      <nav style={{
        background: "#1F497D",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        height: 52,
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      }}>
        <span style={{ color: "#fff", fontWeight: 700, fontSize: 16, marginRight: 32, letterSpacing: 0.5 }}>
          🏛 Future University LIMS
        </span>
        {NAV.map(n => (
          <button
            key={n.key}
            onClick={() => setPage(n.key)}
            style={{
              background: page === n.key ? "rgba(255,255,255,0.15)" : "transparent",
              border: "none",
              color: page === n.key ? "#fff" : "#BDD0E8",
              padding: "0 18px",
              height: 52,
              fontSize: 14,
              fontWeight: page === n.key ? 600 : 400,
              cursor: "pointer",
              borderBottom: page === n.key ? "3px solid #fff" : "3px solid transparent",
              transition: "all 0.2s",
            }}
          >
            {n.label}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <span style={{ color: "#BDD0E8", fontSize: 12, marginRight: 16 }}>
          👤 {username}
        </span>
        <button
          onClick={handleLogout}
          style={{
            background: "rgba(255,255,255,0.1)",
            border: "1px solid rgba(255,255,255,0.2)",
            color: "#fff",
            padding: "6px 14px",
            borderRadius: 6,
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          Sign out
        </button>
      </nav>
      <div>
        {page === "dashboard" && <Dashboard token={token} />}
        {page === "booking"   && <BookingPage token={token} />}
        {page === "needs"     && <NeedsRequestForm token={token} />}
        {page === "users"     && <UsersPage token={token} />}
      </div>
    </div>
  );
}
