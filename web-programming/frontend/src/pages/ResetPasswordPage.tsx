import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api";

const PASSWORD_MSG =
  "Password must be at least 8 characters and include uppercase, lowercase, " +
  "number, and special character. Only English letters, numbers, and symbols are allowed.";

function validatePassword(pw: string): string | null {
  if (pw.length < 8) return PASSWORD_MSG;
  if (/[^\x21-\x7E]/.test(pw)) return PASSWORD_MSG;       // non-ASCII or space
  if (!/[A-Z]/.test(pw)) return PASSWORD_MSG;              // uppercase
  if (!/[a-z]/.test(pw)) return PASSWORD_MSG;              // lowercase
  if (!/[0-9]/.test(pw)) return PASSWORD_MSG;              // digit
  if (!/[!@#$%^&*()\-_=+[\]{}|;:'",.<>?/`~\\]/.test(pw)) return PASSWORD_MSG; // special
  return null;
}

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const pwError = validatePassword(newPassword);
    if (pwError) { setError(pwError); return; }
    if (newPassword !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await resetPassword(token, newPassword);
      setDone(true);
      setTimeout(() => navigate("/login?reset=success"), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="auth-brand">⬡ NucleiAI</div>
          <h2 className="auth-title">Invalid link</h2>
          <p className="field-hint">This reset link is missing or malformed.</p>
          <p className="auth-footer">
            <Link to="/forgot-password" className="link-btn">Request a new link</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">⬡ NucleiAI</div>
        <h2 className="auth-title">Set new password</h2>

        {done ? (
          <p className="field-hint">Password updated! Redirecting to sign in…</p>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <label className="field-label">
              New password <span className="field-hint">(uppercase, lowercase, number, special char)</span>
            </label>
            <input
              className="field-input"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              autoComplete="new-password"
              autoFocus
            />
            <label className="field-label">Confirm new password</label>
            <input
              className="field-input"
              type="password"
              required
              minLength={8}
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              autoComplete="new-password"
            />
            {error && <div className="error">{error}</div>}
            <button className="btn btn-full" type="submit" disabled={busy}>
              {busy ? "Saving…" : "Set new password"}
            </button>
          </form>
        )}

        <p className="auth-footer">
          <Link to="/login" className="link-btn">← Back to sign in</Link>
        </p>
      </div>
    </div>
  );
}
