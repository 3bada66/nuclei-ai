import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page"><div className="status-line"><div className="spinner" /> Loading…</div></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
