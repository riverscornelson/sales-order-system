import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock framer-motion to avoid issues with animations in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: 'div',
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    h5: 'h5',
    p: 'p',
    span: 'span',
    button: 'button',
    pre: 'pre',
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url')
global.URL.revokeObjectURL = vi.fn()

// Mock WebSocket
global.WebSocket = vi.fn().mockImplementation(() => ({
  close: vi.fn(),
  send: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: WebSocket.CONNECTING,
}))

// Global test utilities
export const mockFile = (name: string, type: string = 'application/pdf', size: number = 1024) =>
  new File(['test content'], name, { type, lastModified: Date.now() })

export const mockProcessingCard = {
  id: 'test-card',
  title: 'Test Card',
  status: 'completed' as const,
  content: { message: 'Test content' },
  timestamp: new Date().toISOString(),
}

export const mockOrderData = {
  customer_info: {
    name: 'John Doe',
    email: 'john@example.com',
    company: 'Test Company',
    customer_id: 'CUST001',
  },
  line_items: [
    {
      line_number: 1,
      original_description: 'Steel Rod',
      matched_part_number: 'ST-001',
      quantity: 10,
      unit_price: 25.50,
      line_total: 255.00,
      match_confidence: 0.95,
    },
  ],
  total_amount: 255.00,
}