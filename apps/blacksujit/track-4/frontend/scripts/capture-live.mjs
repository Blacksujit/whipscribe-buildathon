// Capture the live dashboard (real data) into ../docs/screenshots/.
// Usage: node scripts/capture-live.mjs
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const OUT = "D:/Whisp-scribe/whipscribe-buildathon/apps/blacksujit/track-4/docs/screenshots";
const BASE = "https://callcoachai.sujit.top";
const SAMPLE_CALL = "bcfcea2d-b6d7-4cff-b75c-d5e3628ec5e7";

mkdirSync(OUT, { recursive: true });

const shots = [
  { name: "live-home.png", path: "/", full: true },
  { name: "live-trends.png", path: "/trends" },
  { name: "live-coach.png", path: "/coach" },
  { name: "live-speakers.png", path: "/speakers" },
  { name: "live-report.png", path: `/report/${SAMPLE_CALL}`, full: true },
  { name: "live-assistant.png", path: "/assistant", ask: true },
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

for (const shot of shots) {
  try {
    await page.goto(BASE + shot.path, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(2500);
    if (shot.ask) {
      await page.click(".assistant-chip", { timeout: 10000 }).catch(() => {});
      await page.waitForTimeout(1600);
    }
    await page.screenshot({ path: `${OUT}/${shot.name}`, fullPage: !!shot.full });
    console.log("captured", shot.name);
  } catch (error) {
    console.log("FAILED", shot.name, error.message);
  }
}

await browser.close();
