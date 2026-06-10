import { expect, test } from "@playwright/test";

const projectId = "demo-agentops-quality-studio";

test("home and project dashboard expose seeded local artifacts", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "AgentOps Evaluation & Observability Studio" })).toBeVisible();
  await expect(page.getByText("Demo AgentOps Quality Studio")).toBeVisible();
  await page.getByRole("link", { name: "Open dashboard" }).click();
  await expect(page.getByRole("heading", { name: "Demo AgentOps Quality Studio" })).toBeVisible();
  await expect(page.getByText("Run mock eval")).toBeVisible();
  await expect(page.getByText("Latest pass rate")).toBeVisible();
});

test("project subpages render prompts datasets runs and traces", async ({ page }) => {
  await page.goto(`/projects/${projectId}/prompts`);
  await expect(page.getByRole("heading", { name: "Prompt Versions" })).toBeVisible();
  await expect(page.getByText("Customer support agent")).toBeVisible();

  await page.goto(`/projects/${projectId}/datasets`);
  await expect(page.getByRole("heading", { name: "Datasets" })).toBeVisible();
  await expect(page.getByText("prompt_regression_eval")).toBeVisible();

  await page.goto(`/projects/${projectId}/runs`);
  await expect(page.getByRole("heading", { name: "Runs" })).toBeVisible();
  const firstRun = page.locator("tbody a").first();
  await expect(firstRun).toBeVisible();
  await firstRun.click();
  await expect(page.getByText("Estimated cost")).toBeVisible();
  await expect(page.getByText("Open trace").first()).toBeVisible();

  await page.goto(`/projects/${projectId}/traces`);
  await expect(page.getByRole("heading", { name: "Traces" })).toBeVisible();
  const firstTrace = page.locator("tbody a").first();
  await expect(firstTrace).toBeVisible();
  await firstTrace.click();
  await expect(page.getByText("provider.generate").or(page.getByText("mock.answer"))).toBeVisible();
});

test("global dashboards render comparison observability failures reports and settings", async ({ page }) => {
  await page.goto("/compare");
  await expect(page.getByRole("heading", { name: "Run Comparison" })).toBeVisible();

  await page.goto("/observability");
  await expect(page.getByRole("heading", { name: "Observability" })).toBeVisible();
  await expect(page.getByText("Total traces")).toBeVisible();

  await page.goto("/failures");
  await expect(page.getByRole("heading", { name: "Failures" })).toBeVisible();

  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();

  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
  await expect(page.getByText("mock", { exact: true })).toBeVisible();
  await expect(page.getByText("citation_accuracy")).toBeVisible();
});
