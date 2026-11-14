const { app, BrowserWindow, net, protocol, session } = require('electron');
const { join, resolve, sep } = require('node:path');
const { pathToFileURL } = require('node:url');

const origin = 'mathblitz://app';
const webRoot = resolve(__dirname, 'web');
const smoke = process.argv.includes('--smoke-test') && !app.isPackaged;
protocol.registerSchemesAsPrivileged([{ scheme: 'mathblitz', privileges: {
  standard: true, secure: true, supportFetchAPI: true, corsEnabled: true,
} }]);

function permitted(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'mathblitz:' && parsed.host === 'app';
  } catch { return false; }
}

app.whenReady().then(async () => {
  protocol.handle('mathblitz', async (request) => {
    if (!permitted(request.url) || request.method !== 'GET') return new Response(null, { status: 403 });
    const pathname = new URL(request.url).pathname;
    const path = resolve(webRoot, pathname === '/' ? 'index.html' : `.${decodeURIComponent(pathname)}`);
    if (!path.startsWith(`${webRoot}${sep}`)) return new Response(null, { status: 403 });
    try {
      const file = await net.fetch(pathToFileURL(path).href);
      const headers = new Headers(file.headers);
      headers.set('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'");
      return new Response(file.body, { status: file.status, headers });
    } catch { return new Response(null, { status: 404 }); }
  });

  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  const window = new BrowserWindow({
    width: 1220, height: 860, minWidth: 360, minHeight: 540, show: !smoke,
    autoHideMenuBar: true, title: 'MathBlitz',
    webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false, devTools: !app.isPackaged },
  });
  window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  for (const event of ['will-navigate', 'will-redirect']) {
    window.webContents.on(event, (event, url) => { if (!permitted(url)) event.preventDefault(); });
  }
  await window.loadURL(`${origin}/`);
  if (smoke) {
    const result = await window.webContents.executeJavaScript(`(async () => {
      const catalog = await MathBlitzGuest.request('/activities');
      document.getElementById('guest-button').click();
      for (let i = 0; i < 150 && document.getElementById('submit-answer').disabled &&
        document.getElementById('choice-options').classList.contains('hidden'); i++) {
        await new Promise(resolve => setTimeout(resolve, 20));
      }
      const nav = document.querySelector('[data-view="explore"]');
      nav.click();
      return { title: document.title, categories: catalog.activities.length,
        modes: catalog.difficulties.length, nodeAccess: typeof require !== 'undefined',
        explore: nav.getAttribute('aria-current') === 'page' && document.querySelectorAll('.explore-card').length === 12,
        guestOnly: document.getElementById('account-controls').classList.contains('hidden'),
        promptLoaded: document.getElementById('timer-value').textContent !== '--' };
    })()`);
    console.log(JSON.stringify(result));
    app.exit(result.categories === 12 && result.modes === 5 && !result.nodeAccess && result.explore && result.guestOnly && result.promptLoaded ? 0 : 1);
  }
}).catch((error) => { console.error(error); app.exit(1); });

app.on('window-all-closed', () => app.quit());
