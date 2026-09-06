// File: frontend/src/App.jsx | Location: frontend/src/App.jsx
import { useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
} from "react-router-dom";
 
import Lakshmi from "./pages/Laxmi";
import FinTwin from "./pages/FinTwin";
import Saheli from "./pages/Saheli";
import AdminLogin from "./pages/AdminLogin";
 
function App() {
  // Gates the Saheli (NGO admin) dashboard. Not persisted on purpose —
  // resets on refresh, this is a demo-time gate, not real auth.
  const [isAdminAuthed, setIsAdminAuthed] = useState(false);
 
  return (
    <BrowserRouter>
      <nav
        style={{
          padding: "12px 24px",
          background: "#1a1a2e",
          display: "flex",
          gap: 24,
        }}
      >
        <span
          style={{
            color: "#6C63FF",
            fontWeight: 700,
            fontSize: 22,
          }}
        >
          ArthRakshak
        </span>
 
        <Link
          to="/"
          style={{
            color: "#fff",
            textDecoration: "none",
          }}
        >
          Lakshmi
        </Link>
 
        <Link
          to="/fintwin"
          style={{
            color: "#fff",
            textDecoration: "none",
          }}
        >
          FinTwin
        </Link>
 
        {isAdminAuthed && (
          <Link
            to="/saheli"
            style={{
              color: "#fff",
              textDecoration: "none",
            }}
          >
            Saheli
          </Link>
        )}
      </nav>
 
      <Routes>
        <Route
          path="/"
          element={<Lakshmi />}
        />
 
        <Route
          path="/fintwin"
          element={<FinTwin />}
        />
 
        <Route
          path="/saheli"
          element={
            isAdminAuthed ? (
              <Saheli />
            ) : (
              <AdminLogin onSuccess={() => setIsAdminAuthed(true)} />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
 
export default App;