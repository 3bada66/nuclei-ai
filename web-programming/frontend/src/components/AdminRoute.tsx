import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function AdminRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page"><div className="status-line"><div className="spinner" /> Loading…</div></div>;
  if (!user || (user.role !== "manager" && user.role !== "admin")) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
