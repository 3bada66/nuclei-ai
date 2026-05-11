import { Page } from "@playwright/test";

const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

// Track which pages already have debug listeners so we never double-attach.
const _debugged = new WeakSet<Page>();

/** Attach console + network failure listeners once per page. */
export function attachDebugListeners(page: Page): void {
  if (_debugged.has(page)) return;
  _debugged.add(page);

  page.on("console", msg => {
    if (msg.type() === "error") {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });

  page.on("requestfailed", req => {
    console.log(`[REQUEST FAILED] ${req.method()} ${req.url()} — ${req.failure()?.errorText}`);
  });

  page.on("response", async res => {
    if (!res.url().includes("/auth/me") && !res.url().includes("/auth/login")) return;
    try {
      const body = await res.text();
      console.log(`[RESPONSE] ${res.status()} ${res.url()} — ${body.slice(0, 200)}`);
    } catch {
      console.log(`[RESPONSE] ${res.status()} ${res.url()} — (body unavailable)`);
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
  const loginBody = await loginRes.json();
  const token: string = loginBody.access_token ?? "";
  console.log(`[loginAs] login → ${loginRes.status()}, token=${token ? token.slice(0, 20) + "…" : "MISSING"}`);

  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("token", t), token);
  await page.goto("/dashboard", { waitUntil: "networkidle" });
  console.log(`[loginAs] final URL = ${page.url()}`);
}

/** Register + login as admin via API (uses dev-only promote endpoint).
 *  /dev/promote-admin is only registered when ENV != "production" and
 *  requires no auth — it is intentionally an unauthenticated dev utility. */
export async function loginAsAdmin(
  page: Page,
  username: string,
  email: string,
  password = "Password123!"
): Promise<void> {
  attachDebugListeners(page);

  const regRes = await page.request.post(`${API}/auth/register`, {
    data: { username, email, password },
  });
  console.log(`[loginAsAdmin] register → ${regRes.status()} (${username})`);

  await page.request.post(`${API}/dev/promote-admin`, { data: { email } });

  const loginRes = await page.request.post(`${API}/auth/login`, {
    data: { email, password },
  });
  const loginBody = await loginRes.json();
  const token: string = loginBody.access_token ?? "";
  console.log(`[loginAsAdmin] login → ${loginRes.status()}, token=${token ? token.slice(0, 20) + "…" : "MISSING"}`);

  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("token", t), token);
  await page.goto("/dashboard", { waitUntil: "networkidle" });
  console.log(`[loginAsAdmin] final URL = ${page.url()}`);
}

/** Navigate to a page and wait for network idle. */
export async function goto(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "networkidle" });
}
