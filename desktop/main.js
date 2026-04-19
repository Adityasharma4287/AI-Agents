// ============================================================
// SellerPilot AI - Electron Main Process
// Starts the FastAPI Python backend, then opens the dashboard
// ============================================================

const { app, BrowserWindow, Tray, Menu, shell, ipcMain, nativeImage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

let mainWindow = null;
let splashWindow = null;
let tray = null;
let backendProcess = null;

const BACKEND_PORT = 8001;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const isDev = process.argv.includes('--dev');

// ── Backend path (dev vs packaged) ─────────────────────────
function getBackendPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'backend');
  }
  return path.join(process.resourcesPath, 'backend');
}

function getPythonPath() {
  if (isDev) {
    // Use system python in dev
    return 'python';
  }
  // In packaged app, look for bundled python
  const bundled = path.join(process.resourcesPath, 'python', 'python.exe');
  return fs.existsSync(bundled) ? bundled : 'python';
}

// ── Start the FastAPI backend ───────────────────────────────
function startBackend() {
  const backendPath = getBackendPath();
  const python = getPythonPath();

  console.log(`Starting backend: ${python} at ${backendPath}`);

  backendProcess = spawn(python, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT), '--no-access-log'], {
    cwd: backendPath,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    windowsHide: true,
  });

  backendProcess.stdout.on('data', (d) => console.log('[Backend]', d.toString().trim()));
  backendProcess.stderr.on('data', (d) => console.error('[Backend ERR]', d.toString().trim()));
  backendProcess.on('close', (code) => console.log(`Backend exited with code ${code}`));
}

// ── Poll until backend is ready ────────────────────────────
function waitForBackend(retries = 30, interval = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      http.get(`${BACKEND_URL}/health`, (res) => {
        if (res.statusCode === 200) return resolve();
        retry();
      }).on('error', retry);
    };
    const retry = () => {
      if (++attempts >= retries) return reject(new Error('Backend failed to start'));
      setTimeout(check, interval);
    };
    check();
  });
}

// ── Splash Screen ───────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480,
    height: 320,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: { nodeIntegration: false },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.center();
}

// ── Main Window ─────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    show: false,
    title: 'SellerPilot AI',
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    backgroundColor: '#0f0f1a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.loadURL(`${BACKEND_URL}/app`);
  mainWindow.setMenuBarVisibility(false);

  // Load the dashboard HTML directly as fallback
  mainWindow.webContents.on('did-fail-load', () => {
    const dashboardPath = path.join(getBackendPath(), '..', 'frontend', 'dashboard.html');
    if (fs.existsSync(dashboardPath)) {
      mainWindow.loadFile(dashboardPath);
    }
  });

  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('close', (e) => {
    if (tray) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── System Tray ─────────────────────────────────────────────
function createTray() {
  const iconPath = path.join(__dirname, 'assets', 'icon.ico');
  const icon = fs.existsSync(iconPath)
    ? nativeImage.createFromPath(iconPath)
    : nativeImage.createEmpty();

  tray = new Tray(icon);
  tray.setToolTip('SellerPilot AI');

  const menu = Menu.buildFromTemplate([
    {
      label: 'Open SellerPilot AI',
      click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } }
    },
    {
      label: 'Open API Docs',
      click: () => shell.openExternal(`${BACKEND_URL}/docs`)
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        tray = null;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(menu);
  tray.on('double-click', () => {
    if (mainWindow) { mainWindow.show(); mainWindow.focus(); }
  });
}

// ── App Lifecycle ────────────────────────────────────────────
app.whenReady().then(async () => {
  createSplash();
  startBackend();

  try {
    splashWindow && splashWindow.webContents.executeJavaScript(
      `document.getElementById('status').textContent = 'Starting AI backend...'`
    ).catch(() => {});

    await waitForBackend();

    splashWindow && splashWindow.webContents.executeJavaScript(
      `document.getElementById('status').textContent = 'Loading dashboard...'`
    ).catch(() => {});

    createTray();
    createMainWindow();

  } catch (err) {
    console.error('Backend startup failed:', err);
    // Still open, load local HTML
    createTray();
    createMainWindow();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Keep running in tray — do not quit
  }
});

app.on('activate', () => {
  if (mainWindow) mainWindow.show();
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  tray = null;
});

// ── IPC Handlers ─────────────────────────────────────────────
ipcMain.handle('get-backend-url', () => BACKEND_URL);
ipcMain.handle('open-external', (_, url) => shell.openExternal(url));
