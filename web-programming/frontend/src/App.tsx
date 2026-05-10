import { Navigate, Route, Routes } from "react-router-dom";
import AdminRoute from "./components/AdminRoute";
import { ConfirmProvider } from "./components/ConfirmModal";
import DashboardLayout from "./components/DashboardLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import ToastContainer from "./components/ToastContainer";
import { ToastProvider } from "./contexts/ToastContext";
import AboutPage from "./pages/AboutPage";
import AnalyzePage from "./pages/AnalyzePage";
import ContactPage from "./pages/ContactPage";
import ExplorePage from "./pages/ExplorePage";
import FavouritesPage from "./pages/FavouritesPage";
import UserProfilePage from "./pages/UserProfilePage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AdminPage from "./pages/AdminPage";
import Dashboard from "./pages/Dashboard";
import JobDetailPage from "./pages/JobDetailPage";
import LoginPage from "./pages/LoginPage";
import OAuthCallbackPage from "./pages/OAuthCallbackPage";
import ProfilePage from "./pages/ProfilePage";
import RegisterPage from "./pages/RegisterPage";
import TwoFactorSetupPage from "./pages/TwoFactorSetupPage";
import TwoFactorVerifyPage from "./pages/TwoFactorVerifyPage";

export default function App() {
  return (
    <ToastProvider>
      <ConfirmProvider>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/2fa/verify" element={<TwoFactorVerifyPage />} />
          <Route path="/oauth-callback" element={<OAuthCallbackPage />} />

          {/* Protected app routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="analyze" element={<AnalyzePage />} />
              <Route path="jobs/:jobId" element={<JobDetailPage />} />
              <Route path="2fa/setup" element={<TwoFactorSetupPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="explore" element={<ExplorePage />} />
              <Route path="favourites" element={<FavouritesPage />} />
              <Route path="users/:username" element={<UserProfilePage />} />
              <Route path="about" element={<AboutPage />} />
              <Route path="contact" element={<ContactPage />} />

              {/* Admin-only routes */}
              <Route element={<AdminRoute />}>
                <Route path="admin" element={<AdminPage />} />
              </Route>

              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Route>
        </Routes>

        {/* Global overlays */}
        <ToastContainer />
      </ConfirmProvider>
    </ToastProvider>
  );
}
