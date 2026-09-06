// File: frontend/src/pages/Laxmi.jsx | Location: frontend/src/pages/Laxmi.jsx
import { useState, useEffect } from "react";
import axios from "axios";
 
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
 
export default function Laxmi() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
 
  // On first load: fetch all sessions, pick the most recent one (or create one if none exist)
  useEffect(() => {
    const init = async () => {
      try {
        const res = await axios.get(`${API_BASE}/chat/sessions`);
        if (res.data.length > 0) {
          setSessions(res.data);
          selectSession(res.data[0].id, res.data);
        } else {
          await startNewChat();
        }
      } catch (err) {
        // backend unreachable — still let the user type, sendMessage will show the error
        setLoading(false);
      }
    };
    init();
  }, []);
 
  const refreshSessions = async () => {
    try {
      const res = await axios.get(`${API_BASE}/chat/sessions`);
      setSessions(res.data);
      return res.data;
    } catch (err) {
      return sessions;
    }
  };
 
  const selectSession = async (sessionId, sessionList = sessions) => {
    setActiveSessionId(sessionId);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/chat/history/${sessionId}`);
      setMessages(res.data);
    } catch (err) {
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };
 
  const startNewChat = async () => {
    try {
      const res = await axios.post(`${API_BASE}/chat/sessions`);
      const newSession = res.data;
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
      setLoading(false);
    } catch (err) {
      setLoading(false);
    }
  };
 
  const deleteSession = async (sessionId, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_BASE}/chat/sessions/${sessionId}`);
    } catch (err) {
      // ignore — still remove from UI
    }
    const remaining = sessions.filter((s) => s.id !== sessionId);
    setSessions(remaining);
 
    if (sessionId === activeSessionId) {
      if (remaining.length > 0) {
        selectSession(remaining[0].id, remaining);
      } else {
        startNewChat();
      }
    }
  };
 
  const sendMessage = async () => {
    if (!input.trim() || !activeSessionId) return;
 
    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
 
    const currentInput = input;
    setInput("");
 
    try {
      const res = await axios.post(`${API_BASE}/chat`, {
        message: currentInput,
        session_id: activeSessionId,
      });
 
      setMessages((prev) => [...prev, { role: "bot", text: res.data.reply }]);
 
      // pick up the auto-generated title / updated ordering after the first message
      refreshSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Backend not reachable." },
      ]);
    }
  };
 
  return (
    <div style={{ display: "flex", height: "calc(100vh - 60px)" }}>
      {/* Sidebar */}
      <div
        style={{
          width: 260,
          background: "#1a1a2e",
          color: "#fff",
          display: "flex",
          flexDirection: "column",
          padding: 12,
        }}
      >
        <button
          onClick={startNewChat}
          style={{
            padding: "10px 14px",
            borderRadius: 8,
            border: "1px solid #6C63FF",
            background: "transparent",
            color: "#fff",
            cursor: "pointer",
            marginBottom: 12,
            textAlign: "left",
          }}
        >
          + New Chat
        </button>
 
        <div style={{ overflowY: "auto", flex: 1 }}>
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => selectSession(s.id)}
              style={{
                padding: "10px 12px",
                borderRadius: 8,
                marginBottom: 6,
                cursor: "pointer",
                background:
                  s.id === activeSessionId ? "#6C63FF" : "transparent",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: 14,
              }}
            >
              <span
                style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {s.title}
              </span>
              <span
                onClick={(e) => deleteSession(s.id, e)}
                style={{ marginLeft: 8, opacity: 0.6 }}
                title="Delete chat"
              >
                ✕
              </span>
            </div>
          ))}
        </div>
      </div>
 
      {/* Main chat area */}
      <div style={{ flex: 1, maxWidth: 800, margin: "0 auto", padding: 20 }}>
        <h2>Lakshmi — Your Financial Advisor</h2>
 
        <div
          style={{
            height: 450,
            overflowY: "auto",
            border: "1px solid #ccc",
            padding: 15,
            borderRadius: 10,
          }}
        >
          {loading && (
            <div style={{ textAlign: "center", color: "#888", marginTop: 20 }}>
              Loading conversation...
            </div>
          )}
 
          {!loading && messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#888", marginTop: 20 }}>
              Ask Lakshmi anything about savings, credit, loans, or government schemes.
            </div>
          )}
 
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                textAlign: m.role === "user" ? "right" : "left",
                margin: "10px 0",
              }}
            >
              <span
                style={{
                  background: m.role === "user" ? "#6C63FF" : "#f1f1f1",
                  color: m.role === "user" ? "#fff" : "#000",
                  padding: "10px 14px",
                  borderRadius: 18,
                  display: "inline-block",
                }}
              >
                {m.text}
              </span>
            </div>
          ))}
        </div>
 
        <div style={{ display: "flex", gap: 10, marginTop: 15 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask Lakshmi..."
            style={{
              flex: 1,
              padding: "12px",
              borderRadius: 8,
              border: "1px solid #ccc",
            }}
          />
 
          <button
            onClick={sendMessage}
            style={{
              padding: "12px 18px",
              borderRadius: 8,
              border: "none",
              background: "#6C63FF",
              color: "white",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
 