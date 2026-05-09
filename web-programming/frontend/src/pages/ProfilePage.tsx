import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { updateProfile, changePassword, selfUpdateRole } from "../api";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

export default function ProfilePage() {
  const { user, login: authLogin } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  // Profile fields
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [profileBusy, setProfileBusy] = useState(false);

  // Self role switch
  const canSwitchRole = user?.role === "viewer" || user?.role === "researcher";
  const [roleBusy, setRoleBusy] = useState(false);

  // Password fields
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwBusy, setPwBusy] = useState(false);

  async function handleProfileSave(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    const patch: { username?: string; email?: string } = {};
    if (username !== user.username) patch.username = username;
    if (email !== user.email) patch.email = email;
    if (Object.keys(patch).length === 0) {
      toast("No changes to save.", "info");
      return;
    }
    setProfileBusy(true);
    try {
      const updated = await updateProfile(patch);
      // Refresh AuthContext user without changing the token
      const token = localStorage.getItem("token") ?? "";
      authLogin(token, updated);
      toast("Profile updated.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setProfileBusy(false);
    }
  }

  async function handleRoleSwitch(newRole: "viewer" | "researcher") {
    if (!user || newRole === user.role) return;
    setRoleBusy(true);
    try {
      const updated = await selfUpdateRole(newRole);
      const token = localStorage.getItem("token") ?? "";
      authLogin(token, updated);
      toast(`Role changed to ${newRole}.`, "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setRoleBusy(false);
    }
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPw !== confirmPw) {
      toast("New passwords do not match.", "error");
      return;
    }
    setPwBusy(true);
    try {
      await changePassword(currentPw, newPw);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
      toast("Password changed successfully.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setPwBusy(false);
    }
  }

  if (!user) return null;

  return (
    <div className="page" style={{ maxWidth: 560 }}>
      <div className="page-header">
        <div>
          <h2 className="page-title">Account Settings</h2>
          <p className="page-subtitle">Update your profile and password</p>
        </div>
      </div>

      {/* Profile info */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
          <div style={{
            width: 52, height: 52, borderRadius: "50%",
            background: "var(--accent-teal, #3ecfb2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, fontWeight: 700, color: "#000",
          }}>
            {user.username[0].toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600 }}>{user.username}</div>
            <span className={`badge badge-role-${user.role}`} style={{ marginTop: 4 }}>{user.role}</span>
          </div>
        </div>

        <form onSubmit={handleProfileSave}>
          <label className="field-label">Username</label>
          <input
            className="field-input"
            type="text"
            required
            minLength={3}
            maxLength={50}
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoComplete="username"
          />
          <label className="field-label" style={{ marginTop: 12 }}>Email</label>
          <input
            className="field-input"
            type="email"
            required
            value={email}
            onChange={e => setEmail(e.target.value)}
            autoComplete="email"
          />
          <button className="btn" type="submit" disabled={profileBusy} style={{ marginTop: 16 }}>
            {profileBusy ? "Saving…" : "Save Profile"}
          </button>
        </form>
      </div>

      {/* Role switch — viewer/researcher only */}
      {canSwitchRole && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3 style={{ marginBottom: 8 }}>Account Role</h3>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
            Switch between Viewer and Researcher. Your data is not affected.
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            {(["viewer", "researcher"] as const).map(r => (
              <button
                key={r}
                className={`btn${user.role === r ? "" : " btn-secondary"}`}
                disabled={roleBusy || user.role === r}
                onClick={() => handleRoleSwitch(r)}
                style={{ textTransform: "capitalize" }}
              >
                {user.role === r ? `✓ ${r}` : r}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Change password */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3 style={{ marginBottom: 16 }}>Change Password</h3>
        <form onSubmit={handleChangePassword}>
          <label className="field-label">Current password</label>
          <input
            className="field-input"
            type="password"
            required
            value={currentPw}
            onChange={e => setCurrentPw(e.target.value)}
            autoComplete="current-password"
          />
          <label className="field-label" style={{ marginTop: 12 }}>New password</label>
          <input
            className="field-input"
            type="password"
            required
            minLength={8}
            value={newPw}
            onChange={e => setNewPw(e.target.value)}
            autoComplete="new-password"
          />
          <label className="field-label" style={{ marginTop: 12 }}>Confirm new password</label>
          <input
            className="field-input"
            type="password"
            required
            minLength={8}
            value={confirmPw}
            onChange={e => setConfirmPw(e.target.value)}
            autoComplete="new-password"
          />
          <button className="btn" type="submit" disabled={pwBusy} style={{ marginTop: 16 }}>
            {pwBusy ? "Updating…" : "Change Password"}
          </button>
        </form>
      </div>

      {/* 2FA status */}
      <div className="card">
        <h3 style={{ marginBottom: 12 }}>Two-Factor Authentication</h3>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{
            padding: "4px 10px",
            borderRadius: 20,
            fontSize: 12,
            fontWeight: 600,
            background: user.totp_enabled ? "var(--accent-teal, #3ecfb2)" : "var(--border, #2a2a3a)",
            color: user.totp_enabled ? "#000" : "var(--text-muted, #888)",
          }}>
            {user.totp_enabled ? "Enabled" : "Disabled"}
          </span>
          {!user.totp_enabled && (
            <button className="btn btn-secondary" onClick={() => navigate("/2fa/setup")}>
              Set up TOTP →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
