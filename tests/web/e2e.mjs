import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { chromium } from "playwright";

const target = process.env.WENXIAN_WEB_URL ?? "http://127.0.0.1:8000/";
const bundlePath = process.env.WENXIAN_WEB_BUNDLE_PATH;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
const packageInstallerRequests = [];

if (bundlePath) {
  const bundle = await readFile(bundlePath);
  await page.route("**/wenxian-web-packages.tar.gz", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/gzip",
      body: bundle,
    }),
  );
}

page.on("request", (request) => {
  if (/pypi\.org|pythonhosted\.org/i.test(request.url())) {
    packageInstallerRequests.push(request.url());
  }
});
page.on("pageerror", (error) => pageErrors.push(error));
page.on("console", (message) => {
  if (message.type() === "error") console.error(`[browser] ${message.text()}`);
});

try {
  await page.goto(target, { waitUntil: "domcontentloaded", timeout: 60_000 });
  await page.locator("#identifier").fill("10.1063/5.0155600");
  await page.locator("#submit").click();

  await page.locator("#progress-container").waitFor({ state: "visible" });
  await page.waitForFunction(
    () => Number(document.querySelector("#progress-bar")?.value ?? 0) >= 32,
    undefined,
    { timeout: 120_000 },
  );

  await page.locator("#output").waitFor({ state: "visible", timeout: 180_000 });
  const bibtex = (await page.locator("#bibtex").textContent()) ?? "";
  assert.match(bibtex, /^@/);
  assert.match(bibtex.toLowerCase(), /10\.1063\/5\.0155600/);
  assert.equal(await page.locator("#submit").isDisabled(), false);
  assert.deepEqual(pageErrors, []);

  if (bundlePath) {
    assert.deepEqual(
      packageInstallerRequests,
      [],
      `prebuilt path unexpectedly contacted package indexes: ${packageInstallerRequests.join(", ")}`,
    );
  }
} catch (error) {
  await page.screenshot({ path: "web-e2e-failure.png", fullPage: true });
  throw error;
} finally {
  await browser.close();
}
