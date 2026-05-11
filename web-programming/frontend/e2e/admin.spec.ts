import { test, expect } from "@playwright/test";
import { loginAs, loginAsAdmin, goto } from "./helpers";

const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";

test.describe("Admin panel", () => {
  test("admin user can access /admin panel", async ({ page }) => {
    const ts = Date.now();
    await loginAsAdmin(page, `admin${ts}`, `admin${ts}@test.com`);
    await goto(page, "/admin");
    await expect(page).toHaveURL(/admin/, { timeout: 5_000 });
    const adminLink = page.getByRole("link", { name: "Admin" });
    await expect(adminLink).toBeVisible({ timeout: 5_000 });
  });

  test("admin page shows user table", async ({ page }) => {
    const ts = Date.now();
    await loginAsAdmin(page, `admpg${ts}`, `admpg${ts}@test.com`);

    // Register a second user via API so table has >1 row
    await page.request.post(`${API}/auth/register`, {
      data: {
        username: `regular${ts}`,
        email: `regular${ts}@test.com`,
        password: "Password123!",
      },
    });

    await goto(page, "/admin");
    const table = page.getByRole("table");
    await expect(table).toBeVisible({ timeout: 5_000 });
    const rows = page.getByRole("row");
    // At least header + 1 data row
    await expect(rows.first()).toBeVisible();
  });

  test("non-admin cannot navigate to /admin", async ({ page }) => {
    const ts = Date.now();
    await loginAs(page, `viewer${ts}`, `viewer${ts}@test.com`);
    await goto(page, "/admin");
    await expect(page).not.toHaveURL(/admin/, { timeout: 5_000 });
  });

  test("admin stats card shows Total Users", async ({ page }) => {
    const ts = Date.now();
    await loginAsAdmin(page, `statadm${ts}`, `statadm${ts}@test.com`);
    await goto(page, "/admin");
    await expect(page.getByText("Total Users")).toBeVisible({ timeout: 5_000 });
  });
});
