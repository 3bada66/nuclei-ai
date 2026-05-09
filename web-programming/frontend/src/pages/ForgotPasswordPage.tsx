import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { forgotPassword, verifyResetCode } from "../api";

type Step = "email" | "code";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await forgotPassword(email);
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleVerifyCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await verifyResetCode(email, code);
      // res.reset_token is NOT a login token — it only works with /auth/reset-password
      navigate(`/reset-password?token=${encodeURIComponent(res.reset_token)}`);
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
        <h2 className="auth-title">Reset password</h2>

        {step === "email" && (
          <>
            <p className="field-hint" style={{ marginBottom: 16 }}>
              Enter your email and we'll send you a 6-digit verification code.
            </p>
            <form className="auth-form" onSubmit={handleSendCode}>
              <label className="field-label">Email</label>
              <input
                className="field-input"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
              />
              {error && <div className="error">{error}</div>}
              <button className="btn btn-full" type="submit" disabled={busy}>
                {busy ? "Sending…" : "Send verification code"}
              </button>
            </form>
            <p className="auth-footer">
              <Link to="/login" className="link-btn">← Back to sign in</Link>
            </p>
          </>
        )}

        {step === "code" && (
          <>
            <p className="field-hint" style={{ marginBottom: 16 }}>
              A 6-digit code was sent to <strong>{email}</strong>. It expires in 10 minutes.
            </p>
            <form className="auth-form" onSubmit={handleVerifyCode}>
              <label className="field-label">Verification code</label>
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
              <button
                className="btn btn-full"
                type="submit"
                disabled={busy || code.length !== 6}
              >
                {busy ? "Verifying…" : "Verify code"}
              </button>
              <button
                type="button"
                className="link-btn"
                style={{ marginTop: 8, textAlign: "center", display: "block" }}
                onClick={() => { setStep("email"); setCode(""); setError(null); }}
              >
                ← Re-enter email
              </button>
            </form>
            <p className="auth-footer">
              <Link to="/login" className="link-btn">← Back to sign in</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
