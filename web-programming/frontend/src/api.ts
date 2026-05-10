const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";

/** Parse a UTC datetime string from the backend and format it in the user's local timezone. */
export function formatDate(isoStr: string): string {
  const utc = isoStr.endsWith("Z") || isoStr.includes("+") ? isoStr : isoStr + "Z";
  return new Date(utc).toLocaleString();
}

export function formatDateOnly(isoStr: string): string {
  const utc = isoStr.endsWith("Z") || isoStr.includes("+") ? isoStr : isoStr + "Z";
  return new Date(utc).toLocaleDateString();
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AnalysisMetadata {
  original_filename: string;
  mode: string;
  threshold: number | null;
  min_area: number;
  image_size: number;
  processing_ms: number;
  device: string;
}

export interface AnalysisResponse {
  job_id: string;
  status: string;
  message: string;
  cell_count: number;
  input_url: string;
  mask_url: string;
  overlay_url: string;
  metadata: AnalysisMetadata;
}

export interface HealthResponse {
  status: string;
  device: string;
  model_loaded: boolean;
  mode: string;
  load_error: string | null;
}

export type UserRole = "manager" | "admin" | "researcher" | "viewer";

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  totp_enabled: boolean;
  created_at: string;
}

export interface JobSummary {
  id: number;
  job_id: string;
  status: string;
  cell_count: number;
  mode: string;
  original_filename: string;
  created_at: string;
  annotation_count: number;
  publication_id: number | null;
}

export interface PublicationResponse {
  id: number;
  job_id: number;
  job_uid: string;
  user_id: number;
  username: string;
  headline: string;
  description: string;
  cell_count: number;
  mode: string;
  overlay_url: string;
  mask_url: string;
  input_url: string;
  original_filename: string;
  created_at: string;
  is_favourited: boolean;
  comment_count: number;
}

export interface CommentResponse {
  id: number;
  publication_id: number;
  user_id: number;
  username: string;
  text: string;
  created_at: string;
}

export interface NotificationResponse {
  id: number;
  actor_username: string;
  kind: string;
  publication_id: number;
  publication_headline: string;
  read: boolean;
  created_at: string;
}

export interface AnnotationResponse {
  id: number;
  job_id: number;
  user_id: number;
  note: string;
  created_at: string;
}

export interface JobDetail extends JobSummary {
  user_id: number | null;
  input_url: string;
  mask_url: string;
  overlay_url: string;
  processing_ms: number;
  threshold: number | null;
  min_area: number;
  image_size: number;
  device: string;
  annotations: AnnotationResponse[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface TwoFactorRequiredResponse {
  requires_2fa: true;
  temp_token: string;
}

export type LoginResponse = TokenResponse | TwoFactorRequiredResponse;

export interface TotpSetupResponse {
  secret: string;
  uri: string;
}

export interface AdminStats {
  total_users: number;
  users_by_role: Record<string, number>;
  total_jobs: number;
  total_cells: number;
}

// ── Base fetch helpers ────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      if (Array.isArray(err?.detail)) {
        // Pydantic validation errors — extract the human-readable message from each
        detail = err.detail.map((e: { msg: string }) => e.msg.replace(/^Value error, /, "")).join(" ");
      } else if (typeof err?.detail === "string") {
        detail = err.detail;
      }
    } catch { /* keep default */ }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

function authFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  return apiFetch(path, {
    ...init,
    headers: { ...init?.headers, ...authHeaders(token) },
  });
}

function getToken(): string {
  return localStorage.getItem("token") ?? "";
}

// Convenience: reads token automatically from localStorage
function authed<T>(path: string, init?: RequestInit): Promise<T> {
  return authFetch(path, getToken(), init);
}

export function fileUrl(relative: string): string {
  return `${API_BASE}${relative}`;
}

// ── Public endpoints ──────────────────────────────────────────────────────────

export function getHealth(): Promise<HealthResponse> {
  return apiFetch("/api/health");
}

export function register(username: string, email: string, password: string): Promise<UserResponse> {
  return apiFetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function emailOtpSend(email: string): Promise<{ message: string }> {
  return apiFetch("/auth/email-otp/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export function emailOtpVerify(email: string, code: string): Promise<TokenResponse> {
  return apiFetch("/auth/email-otp/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
}

// ── Authenticated endpoints ───────────────────────────────────────────────────

export function getMe(): Promise<UserResponse> {
  return authed("/auth/me");
}

export function logoutApi(): Promise<void> {
  return authed("/auth/logout", { method: "POST" });
}

export function totpSetup(token: string): Promise<TotpSetupResponse> {
  return authFetch("/auth/2fa/setup", token, { method: "POST" });
}

export function totpVerifySetup(token: string, code: string): Promise<UserResponse> {
  return authFetch("/auth/2fa/verify-setup", token, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export function totpVerify(tempToken: string, code: string): Promise<TokenResponse> {
  return authFetch("/auth/2fa/verify", tempToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export function forgotPassword(email: string): Promise<{ message: string }> {
  return apiFetch("/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export function verifyResetCode(
  email: string,
  code: string,
): Promise<{ reset_token: string; message: string }> {
  return apiFetch("/auth/verify-reset-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
}

export function resetPassword(token: string, new_password: string): Promise<{ message: string }> {
  return apiFetch("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password }),
  });
}

export function analyzeImage(file: File): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);
  return authed("/api/analyze", { method: "POST", body: form });
}

export function listJobs(skip = 0, limit = 20): Promise<JobSummary[]> {
  return authed(`/api/jobs?skip=${skip}&limit=${limit}`);
}

export function getJob(jobId: string): Promise<JobDetail> {
  return authed(`/api/jobs/${jobId}`);
}

export function deleteJob(jobId: string): Promise<void> {
  return authed(`/api/jobs/${jobId}`, { method: "DELETE" });
}

export async function exportJobsCsv(): Promise<void> {
  const token = getToken();
  const res = await fetch(`${API_BASE}/api/jobs/export.csv`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Export failed (${res.status})`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "nuclei-jobs.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export function createAnnotation(jobId: string, note: string): Promise<AnnotationResponse> {
  return authed(`/api/jobs/${jobId}/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
}

export function deleteAnnotation(annotationId: number): Promise<void> {
  return authed(`/api/annotations/${annotationId}`, { method: "DELETE" });
}

// ── Explore / Publish / Favourites ───────────────────────────────────────────

export function publishJob(jobId: string, headline: string, description: string): Promise<PublicationResponse> {
  return authed(`/api/jobs/${jobId}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ headline, description }),
  });
}

export function unpublishPublication(pubId: number): Promise<void> {
  return authed(`/api/publications/${pubId}`, { method: "DELETE" });
}

export function getJobPublication(jobId: string): Promise<PublicationResponse> {
  return authed(`/api/jobs/${jobId}/publication`);
}

export function getExplore(): Promise<PublicationResponse[]> {
  return authed("/api/explore");
}

export function addFavourite(pubId: number): Promise<void> {
  return authed(`/api/publications/${pubId}/favourite`, { method: "POST" });
}

export function removeFavourite(pubId: number): Promise<void> {
  return authed(`/api/publications/${pubId}/favourite`, { method: "DELETE" });
}

export function getFavourites(): Promise<PublicationResponse[]> {
  return authed("/api/favourites");
}

// Comments
export function getComments(pubId: number): Promise<CommentResponse[]> {
  return authed(`/api/publications/${pubId}/comments`);
}
export function addComment(pubId: number, text: string): Promise<CommentResponse> {
  return authed(`/api/publications/${pubId}/comments`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}
export function deleteComment(commentId: number): Promise<void> {
  return authed(`/api/comments/${commentId}`, { method: "DELETE" });
}

// Notifications
export function getNotifications(): Promise<NotificationResponse[]> {
  return authed("/api/notifications");
}
export function getUnreadCount(): Promise<{ count: number }> {
  return authed("/api/notifications/unread-count");
}
export function markAllRead(): Promise<void> {
  return authed("/api/notifications/read-all", { method: "POST" });
}

// User profiles
export function getUserPublications(username: string): Promise<PublicationResponse[]> {
  return authed(`/api/users/${username}/publications`);
}

// Re-analyze
export function reanalyzeJob(jobId: string): Promise<import("./api").AnalysisResponse> {
  return authed(`/api/jobs/${jobId}/reanalyze`, { method: "POST" });
}

// PDF report
export async function downloadPdfReport(jobId: string): Promise<void> {
  const token = localStorage.getItem("token") ?? "";
  const tzOffset = -Math.round(new Date().getTimezoneOffset() / 60);
  const res = await fetch(`${(import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000"}/api/jobs/${jobId}/report.pdf?tz_offset=${tzOffset}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    let detail = `Failed to download PDF (${res.status})`;
    try { const e = await res.json(); if (e?.detail) detail = e.detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `nuclei-report-${jobId}.pdf`;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── Admin endpoints ───────────────────────────────────────────────────────────

export function adminListUsers(): Promise<UserResponse[]> {
  return authed("/admin/users");
}

export function adminCreateAdmin(username: string, email: string, password: string): Promise<UserResponse> {
  return authed("/admin/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
}

export function adminUpdateRole(userId: number, role: "viewer" | "researcher" | "admin"): Promise<UserResponse> {
  return authed(`/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}

export function adminDeleteUser(userId: number): Promise<void> {
  return authed(`/admin/users/${userId}`, { method: "DELETE" });
}

export function adminStats(): Promise<AdminStats> {
  return authed("/admin/stats");
}

// ── Profile management ────────────────────────────────────────────────────────

export function selfUpdateRole(role: "viewer" | "researcher"): Promise<UserResponse> {
  return authed("/auth/me/role", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}

export function updateProfile(data: { username?: string; email?: string }): Promise<UserResponse> {
  return authed("/auth/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<UserResponse> {
  return authed("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}
