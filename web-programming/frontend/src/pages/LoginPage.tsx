import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { emailOtpSend, emailOtpVerify, login, type LoginResponse } from "../api";

import { useAuth } from "../contexts/AuthContext";

type Tab = "password" | "email-otp";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";

export default function LoginPage() {
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  const [tab, setTab] = useState<Tab>(params.get("tab") === "email-otp" ? "email-otp" : "password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const resetSuccess = params.get("reset") === "success";
  const oauthError = params.get("error");
  const initialError = oauthError === "email_password_account"
    ? "This email is registered with a password. Please sign in with your email and password below."
    : oauthError === "oauth_no_email"
    ? "OAuth login failed: no email returned. Please try another method."
    : oauthError
    ? "OAuth login failed. Please try again."
    : null;
  const [error, setError] = useState<string | null>(initialError);
  const [busy, setBusy] = useState(false);

  async function handlePasswordLogin(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res: LoginResponse = await login(email, password);
      if ("requires_2fa" in res && res.requires_2fa) {
        sessionStorage.setItem("2fa_temp_token", res.temp_token);
        navigate("/2fa/verify");
        return;
      }
      if ("access_token" in res) {
        authLogin(res.access_token, res.user);
        navigate("/dashboard");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await emailOtpSend(email);
      setOtpSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await emailOtpVerify(email, otpCode);
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
        <h2 className="auth-title">Sign in</h2>
        {resetSuccess && (
          <div className="field-hint" style={{ color: "var(--accent-teal)", marginBottom: 12 }}>
            Password reset successfully. Please log in with your new password.
          </div>
        )}

        <div className="tab-row">
          <button className={`tab-btn${tab === "password" ? " active" : ""}`} onClick={() => setTab("password")}>Password</button>
          <button className={`tab-btn${tab === "email-otp" ? " active" : ""}`} onClick={() => setTab("email-otp")}>Email code</button>
        </div>

        {tab === "password" && (
          <form className="auth-form" onSubmit={handlePasswordLogin}>
            <label className="field-label">Email</label>
            <input className="field-input" type="email" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" />
            <label className="field-label">Password</label>
            <input className="field-input" type="password" required value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" />
            {error && <div className="error">{error}</div>}
            <button className="btn btn-full" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
            <p style={{ textAlign: "center", marginTop: 8 }}>
              <Link to="/forgot-password" className="link-btn" style={{ fontSize: 13 }}>Forgot your password?</Link>
            </p>
          </form>
        )}

        {tab === "email-otp" && !otpSent && (
          <form className="auth-form" onSubmit={handleSendOtp}>
            <label className="field-label">Email</label>
            <input className="field-input" type="email" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" />
            {error && <div className="error">{error}</div>}
            <button className="btn btn-full" type="submit" disabled={busy}>{busy ? "Sending…" : "Send code"}</button>
          </form>
        )}

        {tab === "email-otp" && otpSent && (
          <form className="auth-form" onSubmit={handleVerifyOtp}>
            <p className="field-hint">A 6-digit code was sent to <strong>{email}</strong>.</p>
            <label className="field-label">Verification code</label>
            <input className="field-input field-otp" type="text" inputMode="numeric" pattern="\d{6}" maxLength={6} required value={otpCode} onChange={e => setOtpCode(e.target.value)} autoComplete="one-time-code" />
            {error && <div className="error">{error}</div>}
            <button className="btn btn-full" type="submit" disabled={busy}>{busy ? "Verifying…" : "Verify"}</button>
            <button type="button" className="link-btn" onClick={() => setOtpSent(false)}>← Re-enter email</button>
          </form>
        )}

        <div className="oauth-divider"><span>or continue with</span></div>

        <div className="oauth-row">
          <a href={`${API_BASE}/auth/google`} className="oauth-btn">
            <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/><path fill="none" d="M0 0h48v48H0z"/></svg>
            Google
          </a>
          <a href={`${API_BASE}/auth/github`} className="oauth-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
            GitHub
          </a>
          <a href={`${API_BASE}/auth/dropbox`} className="oauth-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="#0061FF"><path d="M6 2L0 6l6 4-6 4 6 4 6-4-6-4 6-4zm12 0l-6 4 6 4-6 4 6 4 6-4-6-4 6-4zM6 16.5L12 20l6-3.5-6-4z"/></svg>
            Dropbox
          </a>
        </div>

        <p className="auth-footer">
          No account? <Link to="/register" className="link-btn">Register</Link>
        </p>
      </div>
    </div>
  );
}
