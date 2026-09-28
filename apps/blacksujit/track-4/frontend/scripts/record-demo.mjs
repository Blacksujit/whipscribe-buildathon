/**
 * Records a walkthrough of the CallCoach-AI dashboard with Playwright.
 *
 * Prerequisites:
 *   - Flask API on http://localhost:5000        (python app.py)
 *   - Next.js dashboard on http://localhost:3000 (npm run build && npm run start)
 *   - For a full upload run: a WhipScribe key with credits
 *   - npx playwright install chromium
 *
 * Usage:
 *   node scripts/record-demo.mjs                 # uploads src/test_speech.wav and records the full flow
 *   DEMO_JOB=<job-id> node scripts/record-demo.mjs   # records the tour of an existing report (no upload)
 *
 * Output: ../videos/demo/callcoach-demo-<timestamp>.webm
 *         ../videos/demo/record-demo.log (progress + page errors)
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
const EXISTING_JOB = process.env.DEMO_JOB || "";

fs.mkdirSync(OUT_DIR, { recursive: true });
const LOG = path.join(OUT_DIR, "record-demo.log");
const log = (msg) => {
  const line = `[demo] ${new Date().toISOString()} ${msg}`;
  console.log(line);
  try {
    fs.appendFileSync(LOG, line + "\n");
  } catch {
    /* logging must never break the recording */
  }
};
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  fs.writeFileSync(LOG, "");
  log(`starting; base=${BASE} mode=${EXISTING_JOB ? `existing job ${EXISTING_JOB}` : `upload ${AUDIO}`}`);
  if (!EXISTING_JOB && !fs.existsSync(AUDIO)) {
    console.error(`[demo] audio file not found: ${AUDIO}`);
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: OUT_DIR, size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();
  page.on("pageerror", (err) => log(`page error: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") log(`console error: ${msg.text()}`);
  });

  log(`opening ${BASE}`);
  await page.goto(BASE, { waitUntil: "networkidle" });
  await wait(2500);

  if (EXISTING_JOB) {
    log(`opening report ${EXISTING_JOB} from the library`);
    await page.goto(`${BASE}/report/${EXISTING_JOB}`, { waitUntil: "networkidle" });
    await wait(3000);
  } else {
    log(`uploading ${path.basename(AUDIO)}`);
    let handedOff = false;
    for (let attempt = 1; attempt <= 8 && !handedOff; attempt++) {
      await page.setInputFiles("#hero-file-input", AUDIO);
      try {
        await page.waitForFunction(
          () => {
            const text = document.body.innerText || "";
            return text.includes("Transcribe") || text.includes("Score") || text.includes("Report") || !!document.querySelector(".pipeline");
          },
          { timeout: 6000 }
        );
        handedOff = true;
        log(`upload accepted the file (attempt ${attempt})`);
      } catch {
        log(`no UI reaction yet (attempt ${attempt}); retrying`);
        await wait(2500);
      }
    }
    if (!handedOff) log("warning: upload UI reaction never detected; waiting for the report anyway");

    log("waiting for the report page (transcription + scoring)");
    await page.waitForURL(/\/report\//, { timeout: 14 * 60 * 1000 });
    await page.waitForLoadState("networkidle").catch(() => {});
    await wait(3000);
  }
  log(`report page: ${page.url()}`);

  log("scrolling through the evidence dossier");
  for (let i = 0; i < 6; i++) {
    await page.mouse.wheel(0, 600);
    await wait(900);
  }
  await wait(1200);

  for (const route of ["/trends", "/coach", "/speakers", "/connections"]) {
    log(`visiting ${route}`);
    await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
    await wait(2600);
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
  log(`FAILED: ${err && err.message ? err.message : err}`);
  process.exit(1);
});
