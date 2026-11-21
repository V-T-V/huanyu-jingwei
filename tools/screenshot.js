// 寰宇经纬 · CDP 截图（node 22+ 原生 WebSocket）
// 用法: node tools/screenshot.js <URL> <输出.png> [等待ms]
const fs = require("fs");
const { spawn } = require("child_process");
const os = require("os");
const path = require("path");

const EDGE = [
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\msedge.exe",
].find((p) => fs.existsSync(p));

const [url, out, waitMs = "8000"] = [
  process.env.HY_SHOT_URL,
  process.env.HY_SHOT_OUT,
  process.env.HY_SHOT_WAIT || "8000",
];
if (!url || !out) { console.error("need HY_SHOT_URL / HY_SHOT_OUT"); process.exit(2); }

(async () => {
  const port = 9780 + Math.floor(Math.random() * 20);
  const prof = fs.mkdtempSync(path.join(os.tmpdir(), "hyshot-"));
  const proc = spawn(EDGE, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--use-angle=swiftshader",
    `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`,
    "--window-size=1400,900", "about:blank",
  ], { stdio: "ignore" });

  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 60; i++) {
    try { await (await fetch(`${base}/json/version`)).json(); break; }
    catch (e) { await new Promise(r => setTimeout(r, 250)); }
  }
  // 新开 tab
  await fetch(`${base}/json/new?${encodeURIComponent(url)}`, { method: "PUT" });
  await new Promise(r => setTimeout(r, +waitMs));
  const tabs = await (await fetch(`${base}/json`)).json();
  const tab = tabs.find(t => t.url.split("#")[0] === url.split("#")[0].replace(/\/$/, "/")) ||
              tabs.find(t => (t.url || "").startsWith(url.split("#")[0]));
  if (!tab) { console.error("tab not found; tabs=", tabs.map(t => t.url)); process.exit(1); }

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  const send = (id, method, params) => ws.send(JSON.stringify({ id, method, params }));
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id === 1) {
      if (!m.result || !m.result.data) {
        console.error("capture failed:", JSON.stringify(m).slice(0, 300));
        ws.close(); proc.kill(); process.exit(1);
      }
      fs.writeFileSync(out, Buffer.from(m.result.data, "base64"));
      console.log("saved", out);
      ws.close(); proc.kill(); process.exit(0);
    }
  };
  ws.onopen = () => send(1, "Page.captureScreenshot", { format: "png" });
  setTimeout(() => { console.error("timeout"); proc.kill(); process.exit(1); }, 30000);
})();
