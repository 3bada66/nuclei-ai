import { useState } from "react";

export default function ContactPage() {
  const [copied, setCopied] = useState(false);

  function copyEmail() {
    navigator.clipboard.writeText("webprogrammingproject2026@gmail.com");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="page" style={{ maxWidth: 600 }}>
      <div className="page-header">
        <div>
          <h2 className="page-title">Contact Us</h2>
          <p className="page-subtitle">We'd love to hear from you</p>
        </div>
      </div>

      {/* Email */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginBottom: 12 }}>Get in Touch</h3>
        <p style={{ lineHeight: 1.7, color: "var(--text-muted)", marginBottom: 20 }}>
          Have a complaint, suggestion, or just want to say hello? Reach out to us directly
          by email. We read every message and aim to respond within 48 hours.
        </p>
        <div style={{
          display: "flex", alignItems: "center", gap: 12, flexWrap: "nowrap",
          background: "var(--surface-2, #1a1a2e)", borderRadius: 10, padding: "14px 18px",
          overflow: "hidden",
        }}>
          <span style={{ fontSize: 20 }}>✉️</span>
          <span style={{ fontWeight: 500, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", minWidth: 0 }}>webprogrammingproject2026@gmail.com</span>
          <button className="btn btn-secondary" onClick={copyEmail} style={{ fontSize: 13, whiteSpace: "nowrap" }}>
            {copied ? "✓ Copied" : "Copy"}
          </button>
          <a
            href="mailto:webprogrammingproject2026@gmail.com"
            className="btn"
            style={{ fontSize: 13, whiteSpace: "nowrap" }}
          >
            Send Email
          </a>
        </div>
      </div>

      {/* Categories */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginBottom: 16 }}>What can we help with?</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { icon: "🐛", title: "Bug Reports", desc: "Found something that's not working? Tell us exactly what happened and we'll fix it." },
            { icon: "💡", title: "Feature Requests", desc: "Have an idea that would make NucleiAI better? We're always listening." },
            { icon: "🔬", title: "Research Collaboration", desc: "Want to use NucleiAI in your research or integrate it with your workflow?" },
            { icon: "🔒", title: "Security Issues", desc: "Found a security vulnerability? Please disclose it responsibly via email." },
          ].map(({ icon, title, desc }) => (
            <div key={title} style={{
              display: "flex", gap: 14, alignItems: "flex-start",
              background: "var(--surface-2, #1a1a2e)", borderRadius: 10, padding: 14,
            }}>
              <span style={{ fontSize: 22, flexShrink: 0 }}>{icon}</span>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{title}</div>
                <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Response time */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>Response Time</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
          {[
            { label: "Bug Reports", time: "24–48 hrs" },
            { label: "Feature Requests", time: "3–5 days" },
            { label: "Security Issues", time: "< 24 hrs" },
          ].map(({ label, time }) => (
            <div key={label} style={{ textAlign: "center", background: "var(--surface-2, #1a1a2e)", borderRadius: 10, padding: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 18, color: "var(--accent-teal, #3ecfb2)" }}>{time}</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
