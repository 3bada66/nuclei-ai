import { useEffect, useState } from "react";
import {
  adminCreateAdmin,
  adminDeleteUser,
  adminListUsers,
  adminStats,
  adminUpdateRole,
  formatDateOnly,
  type AdminStats,
  type UserResponse,
} from "../api";
import { useConfirm } from "../components/ConfirmModal";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";

const MANAGER_ROLES = ["viewer", "researcher", "admin"] as const;
const ADMIN_ROLES   = ["viewer", "researcher"] as const;
type ChangeableRole = "viewer" | "researcher" | "admin";

interface AddAdminForm { username: string; email: string; password: string }

export default function AdminPage() {
  const { user: me } = useAuth();
  const { toast } = useToast();
  const confirm = useConfirm();

  const isManager = me?.role === "manager";

  const [users, setUsers] = useState<UserResponse[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  // Add Admin modal state (manager only)
  const [showAddAdmin, setShowAddAdmin] = useState(false);
  const [addForm, setAddForm] = useState<AddAdminForm>({ username: "", email: "", password: "" });
  const [addBusy, setAddBusy] = useState(false);

  useEffect(() => {
    Promise.all([adminListUsers(), adminStats()])
      .then(([u, s]) => { setUsers(u); setStats(s); })
      .catch(e => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  // Whether the logged-in user can perform actions on target
  function canModify(target: UserResponse): boolean {
    if (target.id === me?.id) return false;
    if (target.role === "manager") return false;
    if (me?.role === "admin" && target.role === "admin") return false;
    return true;
  }

  async function handleRoleChange(userId: number, newRole: ChangeableRole) {
    setSavingId(userId);
    try {
      const updated = await adminUpdateRole(userId, newRole);
      setUsers(prev => prev.map(u => u.id === userId ? updated : u));
      toast("Role updated.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setSavingId(null);
    }
  }

  async function handleDelete(userId: number, username: string) {
    if (!await confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    try {
      await adminDeleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
      toast("User deleted.", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    }
  }

  async function handleAddAdmin(e: React.FormEvent) {
    e.preventDefault();
    setAddBusy(true);
    try {
      const newAdmin = await adminCreateAdmin(addForm.username, addForm.email, addForm.password);
      setUsers(prev => [...prev, newAdmin]);
      setAddForm({ username: "", email: "", password: "" });
      setShowAddAdmin(false);
      toast(`Admin "${newAdmin.username}" created.`, "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "error");
    } finally {
      setAddBusy(false);
    }
  }

  function roleLockReason(u: UserResponse): string | null {
    if (u.id === me?.id) return "Cannot modify yourself";
    if (u.role === "manager") return "Managers cannot be modified";
    if (me?.role === "admin" && u.role === "admin") return "Admin cannot modify another admin";
    return null;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2 className="page-title">Admin Dashboard</h2>
          <p className="page-subtitle">User management &amp; platform statistics</p>
        </div>
        {isManager && (
          <button className="btn" onClick={() => setShowAddAdmin(true)}>+ Add Admin</button>
        )}
      </div>

      {/* Stats — 7 cards */}
      {stats && (
        <div className="stats-row" style={{ gridTemplateColumns: "repeat(7, 1fr)" }}>
          <div className="stat-card">
            <div className="metric-value">{stats.total_users}</div>
            <div className="metric-caption">Total Users</div>
          </div>
          <div className="stat-card">
            <div className="metric-value" style={{ color: "var(--accent-coral)" }}>
              {stats.users_by_role.manager ?? 0}
            </div>
            <div className="metric-caption">Managers</div>
          </div>
          <div className="stat-card">
            <div className="metric-value" style={{ color: "var(--accent-coral)" }}>
              {stats.users_by_role.admin ?? 0}
            </div>
            <div className="metric-caption">Admins</div>
          </div>
          <div className="stat-card">
            <div className="metric-value" style={{ color: "var(--accent-teal)" }}>
              {stats.users_by_role.researcher ?? 0}
            </div>
            <div className="metric-caption">Researchers</div>
          </div>
          <div className="stat-card">
            <div className="metric-value">{stats.users_by_role.viewer ?? 0}</div>
            <div className="metric-caption">Viewers</div>
          </div>
          <div className="stat-card">
            <div className="metric-value">{stats.total_jobs}</div>
            <div className="metric-caption">Total Jobs</div>
          </div>
          <div className="stat-card">
            <div className="metric-value">{stats.total_cells.toLocaleString()}</div>
            <div className="metric-caption">Cells Counted</div>
          </div>
        </div>
      )}

      {loading && <div className="status-line"><div className="spinner" /> Loading…</div>}
      {error && <div className="error">{error}</div>}

      {/* Users table */}
      {!loading && users.length > 0 && (
        <div className="table-wrap">
          <table className="job-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Joined</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => {
                const lockReason = roleLockReason(u);
                const locked = lockReason !== null;
                return (
                  <tr
                    key={u.id}
                    className="job-row"
                    style={{ cursor: "default", opacity: locked && u.role !== "manager" ? 0.6 : 1 }}
                  >
                    <td><code className="job-id">{u.id}</code></td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{u.username}</span>
                      {u.id === me?.id && (
                        <span className="badge" style={{ marginLeft: 8, fontSize: 11 }}>you</span>
                      )}
                    </td>
                    <td className="filename">{u.email}</td>
                    <td>
                      {canModify(u) ? (
                        <>
                          <select
                            className={`role-select badge badge-role-${u.role}`}
                            value={u.role}
                            disabled={savingId === u.id}
                            onChange={e => handleRoleChange(u.id, e.target.value as ChangeableRole)}
                          >
                            {(isManager ? MANAGER_ROLES : ADMIN_ROLES).map(r => (
                              <option key={r} value={r}>{r}</option>
                            ))}
                          </select>
                          {savingId === u.id && (
                            <span className="spinner" style={{ display: "inline-block", marginLeft: 8, width: 12, height: 12 }} />
                          )}
                        </>
                      ) : (
                        <span className={`badge badge-role-${u.role}`}>{u.role}</span>
                      )}
                    </td>
                    <td className="ts">{formatDateOnly(u.created_at)}</td>
                    <td>
                      {canModify(u) ? (
                        <button
                          className="btn-ghost btn-danger"
                          onClick={() => handleDelete(u.id, u.username)}
                          title="Delete user"
                        >
                          ✕
                        </button>
                      ) : (
                        <span
                          style={{ fontSize: 12, color: "var(--text-muted)", cursor: "help" }}
                          title={lockReason ?? ""}
                        >
                          🔒
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Admin modal — manager only */}
      {showAddAdmin && (
        <div
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
          }}
          onClick={e => { if (e.target === e.currentTarget) setShowAddAdmin(false); }}
        >
          <div className="card" style={{ width: 360, padding: 28 }}>
            <h3 style={{ marginBottom: 20 }}>Create Admin Account</h3>
            <form onSubmit={handleAddAdmin} className="auth-form">
              <label className="field-label">Username</label>
              <input
                className="field-input"
                required
                minLength={3}
                maxLength={50}
                value={addForm.username}
                onChange={e => setAddForm(f => ({ ...f, username: e.target.value }))}
                autoFocus
              />
              <label className="field-label">Email</label>
              <input
                className="field-input"
                type="email"
                required
                value={addForm.email}
                onChange={e => setAddForm(f => ({ ...f, email: e.target.value }))}
              />
              <label className="field-label">Password</label>
              <input
                className="field-input"
                type="password"
                required
                minLength={8}
                value={addForm.password}
                onChange={e => setAddForm(f => ({ ...f, password: e.target.value }))}
              />
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button className="btn btn-full" type="submit" disabled={addBusy}>
                  {addBusy ? "Creating…" : "Create Admin"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-full"
                  onClick={() => setShowAddAdmin(false)}
                  disabled={addBusy}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
