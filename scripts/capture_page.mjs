// Record a real web page for the shop display (N33): a full-page screenshot at the screen's width, saved as an asset
// with a sidecar recording the URL, the capture time and the page title (never overwritten: a new capture of the same
// name stops; archive the old one first).
//
// Usage: node scripts/capture_page.mjs URL OUT.png [--width 1376] [--scale 1.5]
//   (1376 CSS px at 1.5x = 2064 px, the screen's texture width, overlays/screen.json)
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import puppeteer from "puppeteer";

const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const [url, out] = args;
if (existsSync(out)) throw new Error(`${out} exists: archive it before recapturing`);
const width = Number(opt("--width", 1376)), scale = Number(opt("--scale", 1.5));
mkdirSync(dirname(out), { recursive: true });

// --no-sandbox as the project's other Puppeteer scripts: this Ubuntu blocks Chrome's user-namespace sandbox.
const browser = await puppeteer.launch({ headless: "shell", args: ["--no-sandbox"] });
try {
  const p = await browser.newPage();
  await p.setViewport({ width, height: Math.round(width / 1.72), deviceScaleFactor: scale });
  await p.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
  await new Promise(r => setTimeout(r, 1500));  // late fonts and images
  const title = await p.title();
  await p.screenshot({ path: out, fullPage: true });
  const meta = { url, final_url: p.url(), title, captured: new Date().toISOString(), width_css: width, scale };
  writeFileSync(out.replace(/\.png$/, ".json"), JSON.stringify(meta, null, 1) + "\n");
  console.log(JSON.stringify(meta));
} finally {
  await browser.close();
}
