// Render the shop display's screen (overlays/screen.html, overlays/screen.json) to a PNG sequence, one frame per
// 1/30 s of song time, named by the scene frame they show on (f_<frame>.png, frame = song s × fps, sr_anim.frame), for the Blender set
// to map onto shop.screen_page (nursery.shop_twin).
//
// Usage: node overlays/screen.mjs [--out renders/screen] [--at t1,t2,...] [--page file.png]   (--at: stills only)
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import puppeteer from "puppeteer";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const cfg = JSON.parse(readFileSync(join(ROOT, "overlays/screen.json"), "utf8"));
const tm = JSON.parse(readFileSync(join(ROOT, "timing/timing_map.json"), "utf8"));
const FPS = tm.fps;
const shot = Object.fromEntries(tm.shots.map(s => [s.id, s.t]));
const at = ([id, dt]) => shot[id] + dt;

const pageImg = resolve(opt("--page", join(ROOT, cfg.page.image)));  // --page: another screenshot, for checks
const page = { ...cfg.page, from: at(cfg.from), to: at(["N34", 0.0]), image: pathToFileURL(pageImg).href };
const audits = cfg.audits.map(a => ({ ...a, from: at(a.from), to: at(a.to), md: readFileSync(join(ROOT, a.file), "utf8") }));
const T0 = at(cfg.from), T1 = at(cfg.to);
const [W, H] = cfg.size;
const out = opt("--out", "renders/screen");
mkdirSync(out, { recursive: true });

// --no-sandbox as the project's other Puppeteer scripts: this Ubuntu blocks Chrome's user-namespace sandbox, and the
// page only loads local project files.
const browser = await puppeteer.launch({ headless: "shell", args: ["--no-sandbox", "--allow-file-access-from-files"] });
try {
  const p = await browser.newPage();
  await p.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await p.goto(pathToFileURL(join(ROOT, "overlays/screen.html")).href);
  const ok = await p.evaluate(c => setup(c), { ...cfg, page, audits });
  if (!ok) throw new Error("fonts did not load");
  const snap = async (t, file) => {
    await p.evaluate(t => show(t), t);
    writeFileSync(file, await p.screenshot({ clip: { x: 0, y: 0, width: W, height: H }, type: "png" }));
  };
  if (args.includes("--at")) {
    for (const t of opt("--at", "").split(",").map(Number)) await snap(t, join(out, `still_${t.toFixed(2)}.png`));
  } else {
    const f0 = Math.floor(T0 * FPS), f1 = Math.ceil(T1 * FPS);
    for (let f = f0; f <= f1; f++) await snap(f / FPS, join(out, `f_${String(f).padStart(5, "0")}.png`));
    writeFileSync(join(out, "range.json"), JSON.stringify({ first: f0, last: f1, size: cfg.size }) + "\n");
    console.log(`screen: frames ${f0}..${f1} (${f1 - f0 + 1}) -> ${out}`);
  }
} finally {
  await browser.close();
}
