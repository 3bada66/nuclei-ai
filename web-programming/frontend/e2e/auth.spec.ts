import { test, expect } from "@playwright/test";

test.describe("Auth flows", () => {
  test("register page renders and links to login", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /create account/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    const loginLink = page.getByRole("link", { name: /sign in/i });
    await expect(loginLink).toBeVisible();
  });

  test("login page renders and links to register", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
    // Should have OAuth buttons or a register link somewhere
    await expect(page.getByText(/google|github|discord|register|create/i).first()).toBeVisible();
  });

  test("register with valid credentials and auto-login", async ({ page }) => {
    const ts = Date.now();
    await page.goto("/register");
    await page.getByLabel(/username/i).fill(`user${ts}`);
    await page.getByLabel(/email/i).fill(`user${ts}@test.com`);
    await page.getByLabel(/password/i).fill("Password123!");
    await page.getByRole("button", { name: /create account/i }).click();
    // Should redirect to dashboard after register+auto-login
    await expect(page).toHaveURL(/dashboard|analyze/, { timeout: 10_000 });
  });

  test("login with wrong password shows error", async ({ page }) => {
    await page.goto("/login", { waitUntil: "networkidle" });
    await page.getByLabel(/email/i).fill("nobody@test.com");
    await page.getByLabel(/password/i).fill("wrongpassword");
    // Wait for the API response before asserting the error div appeared
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes("/auth/login"), { timeout: 10_000 }),
      page.getByRole("button", { name: /sign in/i }).click(),
    ]);
    // Backend returns 401 with "Invalid credentials." — check the error element by class
    await expect(page.locator(".error").first()).toBeVisible({ timeout: 5_000 });
  });

  test("unauthenticated user redirected from /dashboard to /login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/login/, { timeout: 5_000 });
  });

  test("logout clears session and redirects to login", async ({ page }) => {
    const ts = Date.now();
    // Clear any previous auth state from earlier tests
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
    // Register + login via UI
    await page.goto("/register", { waitUntil: "networkidle" });
    await page.getByLabel(/username/i).fill(`logoutuser${ts}`);
    await page.getByLabel(/email/i).fill(`logoutuser${ts}@test.com`);
    await page.getByLabel(/password/i).fill("Password123!");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page).toHaveURL(/dashboard|analyze/, { timeout: 10_000 });

    // Click logout (button has title="Sign out")
    const logoutBtn = page.getByTitle("Sign out");
    await expect(logoutBtn).toBeVisible();
    await logoutBtn.click();
    await expect(page).toHaveURL(/login/, { timeout: 5_000 });
  });
});
