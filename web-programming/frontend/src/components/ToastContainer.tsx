import { useToast } from "../contexts/ToastContext";

export default function ToastContainer() {
  const { toasts, dismiss } = useToast();
  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: "fixed",
      bottom: 24,
      right: 24,
      display: "flex",
      flexDirection: "column",
      gap: 10,
      zIndex: 9999,
      pointerEvents: "none",
    }}>
      {toasts.map(t => (
        <div
          key={t.id}
          onClick={() => dismiss(t.id)}
          style={{
            pointerEvents: "auto",
            cursor: "pointer",
            padding: "12px 16px",
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            maxWidth: 360,
            boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            background:
              t.type === "success" ? "var(--accent-teal, #3ecfb2)" :
              t.type === "error"   ? "var(--accent-coral, #ff6b6b)" :
                                     "var(--panel-bg, #1e1e2e)",
            color:
              t.type === "success" ? "#000" :
              t.type === "error"   ? "#fff" :
                                     "var(--text, #eee)",
            border: t.type === "info" ? "1px solid var(--border, #2a2a3a)" : "none",
            animation: "slideUp 0.2s ease",
          }}
        >
          <span style={{ flex: 1 }}>{t.message}</span>
          <span style={{ opacity: 0.6, fontSize: 12 }}>✕</span>
        </div>
      ))}
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
