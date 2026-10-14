/* Capturas reales: ejecuta cada operación en GraphiQL y devuelve su respuesta HTTP.
   npm install playwright; npx playwright install chromium
   node scripts/capture_roles.cjs
   python scripts/demo_roles.py --docker --capture-url http://127.0.0.1:8019/capture
   PLAYWRIGHT_MODULE permite usar el runtime de Codex; BROWSER_CHANNEL=msedge usa Edge instalado. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const context = await browser.newContext({ viewport: { width: 1500, height: 1300 }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  let initialized = false, index = 0;
  const dir = path.resolve('docs/evidencias/roles/capturas');
  await fs.mkdir(dir, { recursive: true });
  const server = http.createServer(async (req, res) => {
    try {
      if (req.method !== 'POST' || req.url !== '/capture') { res.writeHead(404).end(); return; }
      let body = '';
      for await (const data of req) body += data;
      const item = JSON.parse(body);
      if (!/^http:\/\/127\.0\.0\.1:(8000|8008)\/graphql$/.test(item.url)) throw new Error('Solo API local del proyecto.');
      if (!initialized) {
        await page.goto(item.url);
        await page.waitForSelector('.CodeMirror', { timeout: 45000 });
        initialized = true;
      }
      await page.getByRole('button', { name: 'Variables', exact: true }).click();
      await page.locator('.CodeMirror').evaluateAll((editors, data) => {
        editors[0].CodeMirror.setValue(data.query);
        editors[1].CodeMirror.setValue(JSON.stringify(data.variables, null, 2));
        editors[2].CodeMirror.setValue(JSON.stringify(data.headers));
      }, item);
      const responsePromise = page.waitForResponse(response => {
        if (response.request().method() !== 'POST') return false;
        try { return response.request().postDataJSON().query === item.query; } catch { return false; }
      });
      await page.getByRole('button', { name: 'Execute query (Ctrl-Enter)', exact: true }).click();
      const response = await responsePromise;
      const actual = await response.json();
      await page.waitForFunction(expected => {
        const result = document.querySelectorAll('.CodeMirror')[3]?.CodeMirror?.getValue();
        try { return JSON.stringify(JSON.parse(result)) === JSON.stringify(expected); } catch { return false; }
      }, actual);
      await page.setViewportSize({ width: 1500, height: Math.max(1000, Math.min(2700,
        130 + JSON.stringify(actual, null, 2).split('\n').length * 23)) });
      const file = `${String(++index).padStart(2, '0')}-${item.title.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase()}.png`;
      await page.screenshot({ path: path.join(dir, file) });
      res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify({
        response: actual, http: response.status(), screenshot: `capturas/${file}`,
      }));
      console.log(`Captura ${index}: ${item.title}`);
    } catch (error) {
      console.error(error.message);
      res.writeHead(500, { 'Content-Type': 'application/json' }).end(JSON.stringify({ error: error.message }));
    }
  });
  server.listen(8019, '127.0.0.1', () => console.log('Capturas listas en http://127.0.0.1:8019/capture'));
  process.on('SIGINT', async () => { await browser.close(); server.close(); process.exit(0); });
})();
