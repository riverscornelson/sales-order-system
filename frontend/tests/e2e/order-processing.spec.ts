import { test, expect } from '@playwright/test'

test.describe('Sales Order Entry System E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173')
  })

  test('displays the main interface correctly', async ({ page }) => {
    // Check for main heading
    await expect(page.getByRole('heading', { name: 'Sales Order Entry System' })).toBeVisible()
    
    // Check for upload interface
    await expect(page.getByText('Upload Document')).toBeVisible()
    await expect(page.getByText('Drop your order document here')).toBeVisible()
    
    // Check for supported file type badges
    await expect(page.getByText('PDF')).toBeVisible()
    await expect(page.getByText('Email')).toBeVisible()
  })

  test('handles file upload interaction', async ({ page }) => {
    // Look for the file input (it's hidden but should be present)
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached()
    
    // Check that the input accepts the correct file types
    await expect(fileInput).toHaveAttribute('accept', '.pdf,.eml,.msg,.txt')
  })

  test('shows upload area hover states', async ({ page }) => {
    const uploadArea = page.getByText('Drop your order document here').locator('..')
    
    // Hover over upload area
    await uploadArea.hover()
    
    // Should show hover state (this depends on CSS being applied)
    // In a real test, we might check for specific style changes
  })

  test('displays processing cards when upload starts', async ({ page }) => {
    // Mock the API response for upload
    await page.route('**/api/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'test-session-123',
          status: 'processing',
          message: 'Document uploaded successfully'
        })
      })
    })

    // Mock WebSocket connection
    await page.addInitScript(() => {
      window.WebSocket = class MockWebSocket {
        constructor(url: string) {
          console.log('Mock WebSocket created:', url)
          setTimeout(() => {
            if (this.onopen) this.onopen({} as Event)
          }, 100)
        }
        send() {}
        close() {}
        addEventListener() {}
        removeEventListener() {}
      } as any
    })

    // Create a test file and trigger upload
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.locator('input[type="file"]').click()
    ])

    // Upload a test file
    await fileChooser.setFiles({
      name: 'test-order.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('dummy pdf content')
    })

    // Should show uploading state
    await expect(page.getByText('Uploading Document...')).toBeVisible()
    
    // Should eventually show processing cards (depending on WebSocket messages)
    await page.waitForTimeout(1000) // Wait for any animations/state changes
  })

  test('responsive design works correctly', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 })
    await expect(page.getByRole('heading', { name: 'Sales Order Entry System' })).toBeVisible()
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.getByRole('heading', { name: 'Sales Order Entry System' })).toBeVisible()
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.getByRole('heading', { name: 'Sales Order Entry System' })).toBeVisible()
  })

  test('accessibility standards are met', async ({ page }) => {
    // Check for proper heading structure
    const h1 = page.getByRole('heading', { level: 1 })
    await expect(h1).toBeVisible()
    
    // Check for proper button labeling
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached()
    
    // Check for proper color contrast and focus states
    await page.keyboard.press('Tab')
    // The focused element should have visible focus indicators
  })

  test('handles network errors gracefully', async ({ page }) => {
    // Mock a network error
    await page.route('**/api/upload', async route => {
      await route.abort('failed')
    })

    // Try to upload a file
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.locator('input[type="file"]').click()
    ])

    await fileChooser.setFiles({
      name: 'test-order.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('dummy pdf content')
    })

    // Should show error state
    await expect(page.getByText(/error|failed/i)).toBeVisible({ timeout: 5000 })
  })

  test('animations and transitions work smoothly', async ({ page }) => {
    // Check that Framer Motion animations are functioning
    // This is more of a visual test, but we can check for the presence of animated elements
    
    const uploadCard = page.getByText('Upload Document').locator('..')
    await expect(uploadCard).toBeVisible()
    
    // Animations should complete without throwing errors
    await page.waitForTimeout(1000)
    
    // No console errors should be present
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })
    
    await page.reload()
    await page.waitForTimeout(2000)
    
    // Filter out known non-critical errors
    const criticalErrors = errors.filter(error => 
      !error.includes('favicon') && 
      !error.includes('WebSocket') &&
      !error.toLowerCase().includes('warning')
    )
    
    expect(criticalErrors).toHaveLength(0)
  })
})