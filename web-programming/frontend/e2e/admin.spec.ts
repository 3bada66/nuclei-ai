import { test, expect } from "@playwright/test";
import { loginAs, goto } from "./helpers";

const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

test.describe("Admin panel", () => {
  test("first registered user is admin and can access /admin", async ({ page }) => {
    // This test only works when run against a fresh DB or when the first user hasn't been created.
    // In CI the backend is reset between test runs, so this is reliable.
    const ts = Date.now();
    const adminEmail = `admin${ts}@test.com`;

    // Register first user (becomes admin)
    await page.goto("/register");
    await page.getByLabel(/username/i).fill(`admin${ts}`);
    await page.getByLabel(/email/i).fill(adminEmail);
    await page.getByLabel(/password/i).fill("Password123!");
    await page.getByRole("button", { name: /register|sign up/i }).click();
    await expect(page).toHaveURL(/dashboard|analyze/, { timeout: 10_000 });

    // Admin nav link should be visible (text: "Admin")
    const adminLink = page.getByRole("link", { name: "Admin" });
    await expect(adminLink).toBeVisible({ timeout: 5_000 });
    await adminLink.click();
    await expect(page).toHaveURL(/admin/, { timeout: 5_000 });
  });

  test("admin page shows user table", async ({ page }) => {
    const ts = Date.now();
    // First user = admin
    await loginAs(page, `admpg${ts}`, `admpg${ts}@test.com`);

    // Register a second user via API so table has >1 row
    await page.request.post(`${API}/auth/register`, {
      data: {
        username: `regular${ts}`,
        email: `regular${ts}@test.com`,
        password: "Password123!",
      },
    });

    await goto(page, "/admin");
    // Table should be present
    const table = page.getByRole("table");
    await expect(table).toBeVisible({ timeout: 5_000 });
    // At least the header row + at least 1 data row
    const rows = page.getByRole("row");
    await expect(rows).toHaveCount(3); // header + 2 data rows (admin + regular)
  });

  test("non-admin cannot navigate to /admin", async ({ page }) => {
    // Register first user (admin), then second user (viewer)
    const ts = Date.now();
    await page.request.post(`${API}/auth/register`, {
      data: {
        username: `firstadm${ts}`,
        email: `firstadm${ts}@test.com`,
        password: "Password123!",
      },
    });

    // Second user = viewer
    await loginAs(page, `viewer${ts}`, `viewer${ts}@test.com`);
    await goto(page, "/admin");
    // Should redirect away from /admin
    await expect(page).not.toHaveURL(/admin/, { timeout: 5_000 });
  });

  test("admin stats card shows Total Users", async ({ page }) => {
    const ts = Date.now();
    await loginAs(page, `statadm${ts}`, `statadm${ts}@test.com`);
    await goto(page, "/admin");
    // The metric caption reads "Total Users"
    await expect(page.getByText("Total Users")).toBeVisible({ timeout: 5_000 });
  });
});
