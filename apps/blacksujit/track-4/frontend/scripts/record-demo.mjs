/**
 * Records a walkthrough of the CallCoach-AI dashboard with Playwright.
 *
 * Prerequisites:
 *   - Flask API on http://localhost:5000        (python app.py)
 *   - Next.js dashboard on http://localhost:3000 (npm run dev)
 *   - A WhipScribe key configured server-side, with credits
 *   - npx playwright install chromium
 *
 * Usage:
 *   node scripts/record-demo.mjs [path-to-audio-file]
 *
 * Output: ../videos/demo/callcoach-demo-<timestamp>.webm
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRACK4 = path.resolve(__dirname, "..", "..");
const OUT_DIR = path.join(TRACK4, "videos", "demo");
const BASE = process.env.DEMO_BASE_URL || "http://localhost:3000";
const AUDIO = process.argv[2] || path.join(TRACK4, "src", "test_speech.wav");

const log = (msg) => console.log(`[demo] ${msg}`);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  if (!fs.existsSync(AUDIO)) {
    console.error(`[demo] audio file not found: ${AUDIO}`);
    process.exit(1);
  }
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: OUT_DIR, size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();

  log(`opening ${BASE}`);
  await page.goto(BASE, { waitUntil: "domcontentloaded" });
  await wait(1500);

  log(`uploading ${path.basename(AUDIO)} (transcription can take minutes)`);
  await page.setInputFiles("#hero-file-input", AUDIO);

  log("waiting for the report page");
  await page.waitForURL(/\/report\//, { timeout: 15 * 60 * 1000 });
  await page.waitForLoadState("networkidle").catch(() => {});
  await wait(2500);

  log("scrolling through the evidence dossier");
  for (let i = 0; i < 6; i++) {
    await page.mouse.wheel(0, 600);
    await wait(900);
  }
  await wait(1200);

  for (const route of ["/trends", "/coach", "/speakers", "/settings"]) {
    log(`visiting ${route}`);
    await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded" });
    await wait(3000);
    await page.mouse.wheel(0, 500);
    await wait(1200);
  }

  const video = page.video();
  await page.close();
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const out = path.join(OUT_DIR, `callcoach-demo-${stamp}.webm`);
  await video.saveAs(out);
  await context.close();
  await browser.close();
  log(`saved ${out}`);
}

main().catch((err) => {
  console.error(`[demo] failed: ${err.message}`);
  process.exit(1);
});
