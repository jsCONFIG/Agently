import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';

const repoRoot = path.resolve(__dirname, '..', '..');

export default defineConfig({
  testDir: path.resolve(repoRoot, 'tests/triggerflow_canvas/e2e'),
  timeout: 90_000,
  expect: {
    timeout: 10_000
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry'
  },
  fullyParallel: true,
  reporter: [['list']],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  webServer: [
    {
      command:
        'python -m uvicorn triggerflow_canvas.backend.main:app --host 0.0.0.0 --port 8000',
      url: 'http://127.0.0.1:8000/api/workflows',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      cwd: repoRoot
    },
    {
      command: 'npm run dev -- --host 0.0.0.0 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      cwd: __dirname
    }
  ]
});
