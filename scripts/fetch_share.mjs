// Fetch a claude.ai/share page with headless Chrome; save innerText, HTML and the chat_snapshots API JSON.
// --no-sandbox: Ubuntu AppArmor blocks Chrome's user-namespace sandbox on this machine.
import puppeteer from 'puppeteer';
import fs from 'fs';
const [url, out] = process.argv.slice(2);
const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0 Safari/537.36');
let snap = null;
page.on('response', async r => {
  if (r.url().includes('/api/chat_snapshots/')) { try { snap = await r.text(); } catch {} }
});
await page.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
await new Promise(r => setTimeout(r, 5000));
fs.writeFileSync(out + '.txt', await page.evaluate(() => document.body.innerText));
fs.writeFileSync(out + '.html', await page.content());
if (snap) fs.writeFileSync(out + '.json', snap);
console.log('title:', await page.title(), 'snapshot:', snap ? snap.length : 'none');
await browser.close();
