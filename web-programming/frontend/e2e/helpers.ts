import { Page } from "@playwright/test";

const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

/** Register + login via API, store token in localStorage. */
export async function loginAs(
  page: Page,
  username: string,
  email: string,
  password = "Password123!"
): Promise<void> {
  await page.request.post(`${API}/auth/register`, {
    data: { username, email, password },
  });
  const res = await page.request.post(`${API}/auth/login`, {
    data: { email, password },
  });
  const body = await res.json();
  const token: string = body.access_token ?? "";
  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("token", t), token);
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
}

/** Navigate to a page and wait for network idle. */
export async function goto(page: Page, path: string): Promise<void> {
  await page.goto(path, { waitUntil: "networkidle" });
}
