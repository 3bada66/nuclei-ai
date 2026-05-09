import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { totpSetup, totpVerifySetup } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function TwoFactorSetupPage() {
  const { login: authLogin, token } = useAuth();
  const navigate = useNavigate();
  const [uri, setUri] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) { navigate("/login"); return; }
    totpSetup(token)
      .then(data => { setUri(data.uri); setSecret(data.secret); })
      .catch(err => setError(err instanceof Error ? err.message : String(err)));
  }, [token, navigate]);

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const user = await totpVerifySetup(token, code);
      authLogin(token, user);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">⬡ NucleiAI</div>
          <h2 className="auth-title" style={{ color: "var(--status-green)" }}>2FA enabled!</h2>
          <p className="field-hint">Your account is now protected with Google Authenticator.</p>
          <button className="btn btn-full" onClick={() => navigate("/dashboard")}>Go to dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">⬡ NucleiAI</div>
        <h2 className="auth-title">Set up 2FA</h2>
        <p className="field-hint" style={{ marginBottom: 16 }}>
          Scan the QR code with Google Authenticator, then enter the 6-digit code to confirm.
        </p>

        {uri && (
          <div className="qr-container">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(uri)}`}
              alt="TOTP QR code"
              width={200}
              height={200}
            />
            <p className="field-hint" style={{ marginTop: 8, wordBreak: "break-all", fontSize: 12 }}>
              Manual key: <code>{secret}</code>
            </p>
          </div>
        )}

        <form className="auth-form" onSubmit={handleVerify} style={{ marginTop: 16 }}>
          <label className="field-label">Authenticator code</label>
          <input
            className="field-input field-otp"
            type="text"
            inputMode="numeric"
            pattern="\d{6}"
            maxLength={6}
            required
            value={code}
            onChange={e => setCode(e.target.value)}
            autoComplete="one-time-code"
          />
          {error && <div className="error">{error}</div>}
          <button className="btn btn-full" type="submit" disabled={busy || code.length !== 6}>
            {busy ? "Confirming…" : "Enable 2FA"}
          </button>
        </form>
      </div>
    </div>
  );
}
