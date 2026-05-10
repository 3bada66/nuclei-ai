import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import NotificationBell from "./NotificationBell";

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
          <NavLink to="/explore" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">◉</span> Explore
          </NavLink>
          <NavLink to="/favourites" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">♡</span> Favourites
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">◎</span> Profile
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">◈</span> About Us
          </NavLink>
          <NavLink to="/contact" className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
            <span className="nav-icon">✉</span> Contact Us
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
                <span className="user-pill-name" style={{ paddingLeft: 8 }}>{user.username}</span>
                <span className={`badge badge-role-${user.role}`} style={{ alignSelf: "flex-start", padding: "2px 8px", fontSize: 11 }}>{user.role}</span>
              </div>
              <div style={{ display: "flex", gap: 4, marginLeft: 8 }}>
                <NotificationBell />
                <button className="btn-ghost" onClick={handleLogout} title="Sign out">↩</button>
              </div>
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
