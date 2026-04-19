// ============================================================
// Preload script - secure bridge between renderer and Node
// ============================================================
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('sellerPilot', {
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  platform: process.platform,
  version: process.env.npm_package_version || '1.0.0',
});
