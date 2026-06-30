import { chromium } from "playwright";
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto("http://localhost:1420/investments?tab=quality", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: "quality_tab_fixed.png", fullPage: true });
  
  const text = await page.locator("table").first().textContent().catch(() => "no table");
  console.log("TABLE TEXT:", text?.substring(0, 500));
  
  const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
  const pageText = await page.textContent("body");
  const uuids = pageText?.match(new RegExp(uuidPattern.source, "gi")) || [];
  console.log("UUIDs visible:", uuids.length === 0 ? "NONE (PASS)" : uuids.join(", "));
  
  await browser.close();
})();
