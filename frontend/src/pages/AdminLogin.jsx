// File: frontend/src/pages/AdminLogin.jsx | Location: frontend/src/pages/AdminLogin.jsx
import { useState } from "react";

// Set VITE_ADMIN_PASSWORD in frontend/.env for local/demo use.
// NOTE: this only gates the UI — it does not protect the /trust-graph
// API itself. Fine for a controlled demo, not for a public deployment.
const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD;

export default function AdminLogin({ onSuccess }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!ADMIN_PASSWORD) {
      setError("Admin password not configured (set VITE_ADMIN_PASSWORD in .env).");
      return;
    }

    if (password === ADMIN_PASSWORD) {
      setError("");
      onSuccess();
    } else {
      setError("Incorrect passcode.");
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "calc(100vh - 60px)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          width: 320,
          padding: 28,
          borderRadius: 12,
          border: "1px solid #ccc",
          textAlign: "center",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Admin Access</h3>
        <p style={{ color: "#666", fontSize: 14, marginTop: -8 }}>
          This dashboard is for NGO admins only.
        </p>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter passcode"
          autoFocus
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid #ccc",
            marginBottom: 12,
            boxSizing: "border-box",
          }}
        />

        <button
          type="submit"
          style={{
            width: "100%",
            padding: "10px 12px",
            borderRadius: 8,
            border: "none",
            background: "#6C63FF",
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Unlock
        </button>

        {error && (
          <p style={{ color: "#c0392b", fontSize: 13, marginBottom: 0 }}>{error}</p>
        )}
      </form>
    </div>
  );
}
