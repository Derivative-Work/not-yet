// Fetch a Suno share page with headless Chrome; save every JSON API response, the HTML and the page text.
// Usage: node scripts/fetch_suno.mjs <suno url> <out_dir>
// --no-sandbox: Ubuntu AppArmor blocks Chrome's user-namespace sandbox on this machine.
import puppeteer from 'puppeteer';
import fs from 'fs';
const [url, out] = process.argv.slice(2);
const browser = await puppeteer.launch({ headless: 'shell', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0 Safari/537.36');
let n = 0;
page.on('response', async r => {
  const ct = r.headers()['content-type'] || '';
  if (ct.includes('json')) { try { fs.writeFileSync(`${out}/resp_${n++}.json`, JSON.stringify({ url: r.url(), body: await r.text() })); } catch {} }
});
await page.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
await new Promise(r => setTimeout(r, 4000));
fs.writeFileSync(`${out}/page.html`, await page.content());
fs.writeFileSync(`${out}/page.txt`, await page.evaluate(() => document.body.innerText));
console.log('final url:', page.url(), 'json responses:', n);
await browser.close();
