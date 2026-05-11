import { Page } from "@playwright/test";

const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

/** Attach console + network failure listeners so errors appear in CI log. */
export function attachDebugListeners(page: Page): void {
  page.on("console", msg => {
    if (msg.type() === "error") {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });
  page.on("requestfailed", req => {
    console.log(`[REQUEST FAILED] ${req.method()} ${req.url()} — ${req.failure()?.errorText}`);
  });
  page.on("response", async res => {
    if (res.url().includes("/auth/me") || res.url().includes("/auth/login")) {
      const status = res.status();
      let body = "";
      try { body = await res.text(); } catch { /* ignore */ }
      console.log(`[RESPONSE] ${res.status()} ${res.url()} — ${body.slice(0, 200)}`);
    }
  });
}

/** Register + login via API, store token in localStorage.
 *  Navigates to /dashboard afterwards to guarantee the React AuthContext
 *  has finished its getMe() call before the test starts interacting. */
export async function loginAs(
  page: Page,
  username: string,
  email: string,
  password = "Password123!"
): Promise<void> {
  attachDebugListeners(page);

  const regRes = await page.request.post(`${API}/auth/register`, {
    data: { username, email, password },
  });
  console.log(`[loginAs] register → ${regRes.status()} (${username} / ${email})`);

  const loginRes = await page.request.post(`${API}/auth/login`, {
    data: { email, password },
  });
  const body = await loginRes.json();
  const token: string = body.access_token ?? "";
  console.log(`[loginAs] login → ${loginRes.status()}, token=${token ? token.slice(0, 20) + "…" : "MISSING"}`);

  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("token", t), token);
  await page.goto("/dashboard", { waitUntil: "networkidle" });
  console.log(`[loginAs] final URL = ${page.url()}`);
}

/** Register + login as admin via API (uses dev-only promote endpoint). */
export async function loginAsAdmin(
  page: Page,
  username: string,
  email: string,
  password = "Password123!"
): Promise<void> {
  await page.request.post(`${API}/auth/register`, {
    data: { username, email, password },
  });
  // Promote to admin via dev-only endpoint
  await page.request.post(`${API}/dev/promote-admin`, {
    data: { email },
  });
  const res = await page.request.post(`${API}/auth/login`, {
    data: { email, password },
  });
  const body = await res.json();
  const token: string = body.access_token ?? "";
  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("token", t), token);
  await page.goto("/dashboard", { waitUntil: "networkidle" });
}

/** Navigate to a page and wait for network idle. */
export async function goto(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "networkidle" });
}
