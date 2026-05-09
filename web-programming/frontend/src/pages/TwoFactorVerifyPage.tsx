import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { totpVerify } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function TwoFactorVerifyPage() {
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const tempToken = sessionStorage.getItem("2fa_temp_token") ?? "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!tempToken) { navigate("/login"); return; }
    setBusy(true);
    setError(null);
    try {
      const res = await totpVerify(tempToken, code);
      sessionStorage.removeItem("2fa_temp_token");
      authLogin(res.access_token, res.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">⬡ NucleiAI</div>
        <h2 className="auth-title">Two-factor verification</h2>
        <p className="field-hint" style={{ marginBottom: 20 }}>
          Open Google Authenticator and enter the 6-digit code.
        </p>
        <form className="auth-form" onSubmit={handleSubmit}>
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
            autoFocus
          />
          {error && <div className="error">{error}</div>}
          <button className="btn btn-full" type="submit" disabled={busy || code.length !== 6}>
            {busy ? "Verifying…" : "Verify"}
          </button>
        </form>

        <p className="field-hint" style={{ marginTop: 24, textAlign: "center", fontSize: 13 }}>
          Can't access your authenticator?{" "}
          <button
            className="link-btn"
            onClick={() => {
              sessionStorage.removeItem("2fa_temp_token");
              navigate("/login?tab=email-otp");
            }}
          >
            Sign in with email code instead
          </button>
        </p>
      </div>
    </div>
  );
}
