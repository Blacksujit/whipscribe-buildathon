/**
 * Captures full-page screenshots of every dashboard route for the README.
 *
 * Usage: node scripts/capture-screenshots.mjs <job-id>
 * Output: ../docs/screenshots/*.png
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRACK4 = path.resolve(__dirname, "..", "..");
const OUT_DIR = path.join(TRACK4, "docs", "screenshots");
const BASE = process.env.DEMO_BASE_URL || "http://localhost:3000";
const JOB = process.argv[2] || "";

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const routes = [
    ["/", "home"],
    ...(JOB ? [[`/report/${JOB}`, "report"]] : []),
    ["/trends", "trends"],
    ["/coach", "coach"],
    ["/speakers", "speakers"],
    ["/connections", "connections"],
  ];

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  for (const [route, name] of routes) {
    await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
    await wait(2200);
    const file = path.join(OUT_DIR, `${name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    console.log(`[shots] saved ${file}`);
  }

  await context.close();
  await browser.close();
}

main().catch((err) => {
  console.error(`[shots] failed: ${err.message}`);
  process.exit(1);
});
