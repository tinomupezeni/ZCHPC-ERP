const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const axios = require('axios');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 8000;
const HEALTH_CHECK_URL = `http://127.0.0.1:${BACKEND_PORT}/api/v2/health/`;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false // Don't show until backend is ready
  });

  // In production, we load from the bundled React build
  // In development, we might load from localhost:3000
  const isDev = process.env.NODE_ENV === 'development';
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'ui_dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });
}

function startBackend() {
  console.log('Starting backend process...');
  
  let backendPath;
  if (app.isPackaged) {
    // In packaged app, the backend is in the resources folder
    backendPath = path.join(process.resourcesPath, 'backend', 'zchpc_backend.exe');
  } else {
    // In development, we use the compiled exe from Phase 2
    // For now, assuming it's in a known location relative to the shell
    backendPath = path.join(__dirname, '..', 'erp_project', 'dist', 'backend_dist', 'zchpc_backend');
    // If not on Windows, we might want to run the python script directly for dev
    if (process.platform !== 'win32') {
      backendPath = 'python';
      const args = [path.join(__dirname, '..', 'erp_project', 'desktop_entrypoint.py')];
      backendProcess = spawn(backendPath, args, {
        env: { ...process.env, USE_SQLITE: 'True', PORT: BACKEND_PORT }
      });
      setupBackendLogging();
      return;
    }
  }

  backendProcess = spawn(backendPath, [], {
    env: { ...process.env, USE_SQLITE: 'True', PORT: BACKEND_PORT }
  });

  setupBackendLogging();
}

function setupBackendLogging() {
  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

async function waitForBackend() {
  console.log('Waiting for backend health check...');
  let retries = 0;
  const maxRetries = 30; // 30 seconds total
  
  while (retries < maxRetries) {
    try {
      const response = await axios.get(HEALTH_CHECK_URL);
      if (response.status === 200) {
        console.log('Backend is healthy!');
        createWindow();
        return;
      }
    } catch (error) {
      // Backend not ready yet
    }
    
    retries++;
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.error('Backend failed to start in time.');
  app.quit();
}

app.whenReady().then(() => {
  startBackend();
  waitForBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (backendProcess) {
    console.log('Terminating backend process...');
    backendProcess.kill();
  }
});
