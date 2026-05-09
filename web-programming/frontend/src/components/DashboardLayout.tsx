import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">⬡</span>
          <span className="brand-name">NucleiAI</span>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/dashboard" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">◫</span> Dashboard
          </NavLink>
          <NavLink to="/analyze" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">⊕</span> Analyze
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">◎</span> Profile
          </NavLink>
          {(user?.role === "manager" || user?.role === "admin") && (
            <NavLink to="/admin" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
              <span className="nav-icon">⚙</span> Admin
            </NavLink>
          )}
        </nav>

        <div className="sidebar-footer">
          {user && (
            <div className="user-pill">
              <div className="user-pill-info">
                <span className="user-pill-name">{user.username}</span>
                <span className={`badge badge-role-${user.role}`}>{user.role}</span>
              </div>
              <button className="btn-ghost" onClick={handleLogout} title="Sign out">↩</button>
            </div>
          )}
        </div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
