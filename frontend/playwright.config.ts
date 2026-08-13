import { defineConfig, devices } from "@playwright/test";
import { createHash } from "node:crypto";

const e2eToken = "operator.e2e-only-agentops-token-secret";
const e2eDigest = createHash("sha256").update(e2eToken.split(".", 2)[1]).digest("hex");

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { open: "never", outputFolder: "../output/playwright-report" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3765",
    trace: "on-first-retry",
    screenshot: "only-on-failure"
  },
  webServer: [
    {
      command: "cd ../backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8765",
      url: "http://127.0.0.1:8765/health",
      reuseExistingServer: true,
      env: {
        CORS_ORIGINS: "http://127.0.0.1:3765,http://localhost:3765",
        API_TOKENS: `operator:operator:${e2eDigest}`
      },
      timeout: 30_000
    },
    {
      command: "npm run dev -- -H 127.0.0.1 -p 3765",
      url: "http://127.0.0.1:3765",
      reuseExistingServer: true,
      env: {
        AGENTOPS_API_BASE_INTERNAL: "http://127.0.0.1:8765",
        AGENTOPS_API_TOKEN: e2eToken
      },
      timeout: 60_000
    }
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } }
    },
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 7"] }
    }
  ]
});
