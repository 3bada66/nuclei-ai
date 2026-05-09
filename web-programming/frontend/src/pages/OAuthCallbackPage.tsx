import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getMe } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function OAuthCallbackPage() {
  const { login: authLogin } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      navigate("/login?error=oauth_failed");
      return;
    }
    localStorage.setItem("token", token);
    getMe()
      .then(user => {
        authLogin(token, user);
        navigate("/dashboard");
      })
      .catch(() => {
        localStorage.removeItem("token");
        navigate("/login?error=oauth_failed");
      });
  }, [params, authLogin, navigate]);

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="status-line"><div className="spinner" /> Completing sign-in…</div>
      </div>
    </div>
  );
}
