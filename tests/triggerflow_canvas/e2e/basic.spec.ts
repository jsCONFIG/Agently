import { expect, test } from '@playwright/test';

test('用户可以拖拽、配置并执行工作流', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByText('TriggerFlow Canvas')).toBeVisible();

  await page.getByRole('button', { name: 'HTTP 触发器' }).first().click();

  const canvasNode = page.locator('.canvas-node').first();
  await expect(canvasNode).toBeVisible();

  const initialLeft = await canvasNode.evaluate((element) => (element as HTMLElement).style.left);
  const boundingBox = await canvasNode.boundingBox();
  if (!boundingBox) {
    throw new Error('Failed to measure canvas node');
  }

  await canvasNode.hover();
  await page.mouse.down();
  await page.mouse.move(boundingBox.x + 200, boundingBox.y + 160, { steps: 5 });
  await page.mouse.up();

  await expect.poll(async () => canvasNode.evaluate((element) => (element as HTMLElement).style.left)).not.toBe(
    initialLeft
  );

  await page.getByLabel('method').fill('GET');
  await page.getByLabel('path').fill('/playwright');

  await page.getByLabel('名称').fill('Playwright 测试流程');
  await page.getByLabel('描述').fill('自动化 E2E 测试');

  await page.getByRole('button', { name: '保存流程' }).click();

  await expect(page.locator('.workflow-list').getByText('Playwright 测试流程')).toBeVisible();

  await page.getByRole('button', { name: '执行流程' }).click();

  await expect(page.getByText(/工作流执行完成/)).toBeVisible({ timeout: 15000 });
});
