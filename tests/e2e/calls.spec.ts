import { test, expect } from '@playwright/test';

test.describe('Call Management Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/');
  });

  test('should display call list', async ({ page }) => {
    await expect(page.locator('text=Calls')).toBeVisible();
    // Call list should be visible
    await expect(page.locator('[data-testid="call-list"]')).toBeVisible();
  });

  test('should open call detail when clicking a call', async ({ page }) => {
    // Wait for calls to load
    await page.waitForSelector('[data-testid="call-item"]', { timeout: 5000 });
    
    // Click first call
    await page.click('[data-testid="call-item"]:first-child');
    
    // Call detail should be visible
    await expect(page.locator('[data-testid="call-detail"]')).toBeVisible();
  });
});

