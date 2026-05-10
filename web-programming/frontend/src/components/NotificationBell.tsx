import { useEffect, useRef, useState } from "react";
import { getNotifications, getUnreadCount, markAllRead, formatDate, type NotificationResponse } from "../api";
import { useNavigate } from "react-router-dom";

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [notifs, setNotifs] = useState<NotificationResponse[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getUnreadCount().then(r => setCount(r.count)).catch(() => {});
    const interval = setInterval(() => {
      getUnreadCount().then(r => setCount(r.count)).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function handleOpen() {
    if (!open) {
      const n = await getNotifications();
      setNotifs(n);
      if (count > 0) {
        await markAllRead();
        setCount(0);
      }
    }
    setOpen(o => !o);
  }

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={handleOpen}
        className="btn-ghost"
        style={{ position: "relative", fontSize: 18, padding: "6px 8px" }}
        title="Notifications"
      >
        🔔
        {count > 0 && (
          <span style={{
            position: "absolute", top: 2, right: 2,
            background: "#ef4444", color: "#fff",
            borderRadius: "50%", width: 16, height: 16,
            fontSize: 10, display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 700,
          }}>
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div style={{
          position: "absolute", bottom: "100%", left: 0, marginBottom: 8,
          width: 300, background: "var(--surface, #12121e)",
          border: "1px solid var(--border, #2a2a3a)", borderRadius: 12,
          boxShadow: "0 8px 32px rgba(0,0,0,0.4)", zIndex: 200, overflow: "hidden",
        }}>
          <div style={{ padding: "12px 16px", fontWeight: 600, fontSize: 13, borderBottom: "1px solid var(--border, #2a2a3a)" }}>
            Notifications
          </div>
          {notifs.length === 0 ? (
            <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>No notifications yet.</div>
          ) : (
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              {notifs.map((n, i) => (
                <div
                  key={n.id}
                  onClick={() => { setOpen(false); navigate("/explore"); }}
                  style={{
                    padding: "10px 16px", cursor: "pointer", fontSize: 13,
                    borderBottom: i < notifs.length - 1 ? "1px solid var(--border, #2a2a3a)" : "none",
                    background: n.read ? "transparent" : "rgba(62,207,178,0.06)",
                  }}
                >
                  <strong>{n.actor_username}</strong>{" "}
                  {n.kind === "favourite" ? "saved" : "commented on"}{" "}
                  <em>"{n.publication_headline}"</em>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    {formatDate(n.created_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
