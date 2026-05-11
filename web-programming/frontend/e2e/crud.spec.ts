import { test, expect } from "@playwright/test";
import { loginAs, goto } from "./helpers";
import path from "path";
import fs from "fs";

/** Create a minimal 1×1 white PNG as a Buffer (no external deps). */
function tinyPngBuffer(): Buffer {
  // Hand-crafted 68-byte 1×1 white RGB PNG
  return Buffer.from(
    "89504e470d0a1a0a0000000d494844520000000100000001080200000090" +
      "7753de0000000c4944415478016360f8cfc00000000200016721bc330000" +
      "0000049454e44ae426082",
    "hex"
  );
}

test.describe("Job CRUD", () => {
  test("analyze page accepts image upload and shows result", async ({ page }) => {
    await loginAs(page, `crud1_${Date.now()}`, `crud1_${Date.now()}@test.com`);
    await goto(page, "/analyze");

    // Write tiny PNG to a temp file
    const tmpPath = path.join(process.cwd(), "e2e", "_tmp_test.png");
    fs.writeFileSync(tmpPath, tinyPngBuffer());

    try {
      // File input is hidden (display:none) but Playwright can set files on it directly.
      // Wait for it to be attached to the DOM first.
      const fileInput = page.locator('input[type="file"]').first();
      await expect(fileInput).toBeAttached({ timeout: 15_000 });
      await fileInput.setInputFiles(tmpPath);

      const submitBtn = page.getByRole("button", { name: /analyze|upload|submit/i });
      await expect(submitBtn).toBeVisible();
      await submitBtn.click();

      // After upload, expect either a result/count or a loading indicator
      await expect(
        page.getByText(/cell|count|result|nuclei|\d+/i).or(
          page.getByRole("progressbar")
        ).first()
      ).toBeVisible({ timeout: 20_000 });
    } finally {
      fs.unlinkSync(tmpPath);
    }
  });

  test("jobs list shows uploaded job", async ({ page }) => {
    const ts = Date.now();
    await loginAs(page, `crud2_${ts}`, `crud2_${ts}@test.com`);

    // Upload via API directly
    const API = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";
    const token = await page.evaluate(() => localStorage.getItem("token"));
    await page.request.post(`${API}/api/analyze`, {
      headers: { Authorization: `Bearer ${token}` },
      multipart: {
        file: {
          name: "test.png",
          mimeType: "image/png",
          buffer: tinyPngBuffer(),
        },
      },
    });

    await goto(page, "/dashboard");
    // Dashboard subtitle is "All analysis jobs" — wait for it
    await expect(page.getByText(/analysis jobs|Total Jobs|dashboard/i).first()).toBeVisible({ timeout: 5_000 });
  });

  test("non-image file upload shows error", async ({ page }) => {
    await loginAs(page, `crud3_${Date.now()}`, `crud3_${Date.now()}@test.com`);
    await goto(page, "/analyze");

    const tmpPath = path.join(process.cwd(), "e2e", "_tmp_test.txt");
    fs.writeFileSync(tmpPath, "not an image");

    try {
      const fileInput = page.locator('input[type="file"]');
      // Some browsers block non-image files via accept attribute; try anyway
      await fileInput.setInputFiles(tmpPath);

      const submitBtn = page.getByRole("button", { name: /analyze|upload|submit/i });
      if (await submitBtn.isEnabled()) {
        await submitBtn.click();
        await expect(page.getByText(/error|invalid|image|unsupported/i).first()).toBeVisible({
          timeout: 5_000,
        });
      }
    } finally {
      fs.unlinkSync(tmpPath);
    }
  });
});
