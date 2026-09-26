const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  console.log("=== VISUAL VERIFICATION ===");
  const routes = [
    { path: "/", name: "Homepage" },
    { path: "/coach", name: "Coach" },
    { path: "/trends", name: "Trends" },
    { path: "/speakers", name: "Speakers" },
    { path: "/settings", name: "Settings" },
    { path: "/report/c32a3520-7a54-4efc-9d7d-c9f15e6d0461", name: "Report" },
  ];

  for (const route of routes) {
    const before = errors.length;
    await page.goto("http://localhost:3000" + route.path);
    await page.waitForTimeout(2000);
    const newErrors = errors.slice(before);
    const status = newErrors.length === 0 ? "PASS" : "FAIL";
    console.log(status + " " + route.name);
    if (newErrors.length > 0) console.log("   ERR: " + newErrors[0].substring(0, 120));
  }

  // Check homepage hero
  await page.goto("http://localhost:3000");
  await page.waitForTimeout(1500);
  const heroCheck = await page.evaluate(() => {
    const h1 = document.querySelector("h1");
    if (!h1) return "no h1 found";
    const style = window.getComputedStyle(h1);
    return "text: " + (h1.textContent || "").substring(0,40) + 
      ", bg: " + (style.backgroundImage !== "none" ? "GRADIENT" : "plain");
  });
  console.log("\nHomepage hero: " + heroCheck);

  // Check brand name
  const brandCheck = await page.evaluate(() => {
    const nav = document.querySelector("nav");
    return nav ? nav.textContent.substring(0, 40) : "no nav";
  });
  console.log("Brand: " + brandCheck);

  console.log("\nTotal errors: " + errors.length);
  if (errors.length === 0) console.log("ALL CLEAN");
  await browser.close();
})();
