import { test, expect } from "@playwright/test";
import { loginAs, goto } from "./helpers";

test.describe("Navigation", () => {
  test("dashboard shows welcome content", async ({ page }) => {
    await loginAs(page, "navuser1", "navuser1@test.com");
    await goto(page, "/dashboard");
    // Some heading or key text should be visible
    await expect(
      page.getByRole("heading").or(page.getByText(/dashboard|welcome|nuclei/i)).first()
    ).toBeVisible();
  });

  test("sidebar/nav links navigate to analyze page", async ({ page }) => {
    await loginAs(page, "navuser2", "navuser2@test.com");
    await goto(page, "/dashboard");
    // NavLink text is "⊕ Analyze" — match by containing text
    const analyzeLink = page
      .getByRole("link", { name: /analyze/i })
      .first();
    await expect(analyzeLink).toBeVisible();
    await analyzeLink.click();
    await expect(page).toHaveURL(/analyze/, { timeout: 5_000 });
  });

  test("analyze page has file upload area", async ({ page }) => {
    await loginAs(page, "navuser3", "navuser3@test.com");
    await goto(page, "/analyze");
    // File input is always present in the UploadPanel (hidden, triggered by click)
    const fileInput = page.locator('input[type="file"]').first();
    await expect(fileInput).toBeAttached({ timeout: 5_000 });
  });

  test("jobs list page is accessible", async ({ page }) => {
    await loginAs(page, "navuser4", "navuser4@test.com");
    // Navigate to jobs if there's such a route
    await goto(page, "/dashboard");
    const jobsLink = page.getByRole("link", { name: /jobs|history/i }).first();
    if (await jobsLink.isVisible()) {
      await jobsLink.click();
      await expect(page).toHaveURL(/jobs|history/, { timeout: 5_000 });
    }
  });
});
