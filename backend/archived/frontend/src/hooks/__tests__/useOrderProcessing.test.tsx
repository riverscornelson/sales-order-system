import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useOrderProcessing } from '../useOrderProcessing'
import { ProcessingStatus } from '../../types/api'
import { mockFile, mockProcessingCard } from '../../test/setup'

// Mock the API service
vi.mock('../../services/api', () => ({
  apiService: {
    uploadDocument: vi.fn(),
    submitOrder: vi.fn(),
    getSessionStatus: vi.fn(),
  },
}))

// Mock the WebSocket hook
vi.mock('../useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    subscribeToSession: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendMessage: vi.fn(),
    isConnected: true,
  })),
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useOrderProcessing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    expect(result.current.sessionId).toBeNull()
    expect(result.current.cards).toEqual([])
    expect(result.current.isProcessing).toBe(false)
    expect(result.current.isUploading).toBe(false)
    expect(result.current.isSubmitting).toBe(false)
    expect(result.current.hasActiveSession).toBe(false)
    expect(result.current.canSubmit).toBe(false)
    expect(result.current.hasErrors).toBe(false)
  })

  it('uploads document successfully', async () => {
    const { apiService } = await import('../../services/api')
    const mockResponse = { session_id: 'test-session-123', message: 'Upload successful' }
    vi.mocked(apiService.uploadDocument).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    const testFile = mockFile('test.pdf')
    
    act(() => {
      result.current.uploadDocument(testFile)
    })

    expect(result.current.isUploading).toBe(true)

    await waitFor(() => {
      expect(result.current.sessionId).toBe('test-session-123')
      expect(result.current.hasActiveSession).toBe(true)
      expect(result.current.isProcessing).toBe(true)
    })

    // Should add upload card
    expect(result.current.cards).toHaveLength(1)
    expect(result.current.cards[0].id).toBe('upload')
    expect(result.current.cards[0].status).toBe(ProcessingStatus.COMPLETED)
  })

  it('handles upload error', async () => {
    const { apiService } = await import('../../services/api')
    vi.mocked(apiService.uploadDocument).mockRejectedValue(new Error('Upload failed'))

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    const testFile = mockFile('test.pdf')
    
    act(() => {
      result.current.uploadDocument(testFile)
    })

    await waitFor(() => {
      expect(result.current.cards).toHaveLength(1)
      expect(result.current.cards[0].id).toBe('upload-error')
      expect(result.current.cards[0].status).toBe(ProcessingStatus.ERROR)
      expect(result.current.hasErrors).toBe(true)
    })
  })

  it('submits order successfully', async () => {
    const { apiService } = await import('../../services/api')
    const mockResponse = { order_id: 'ORD-123', message: 'Order submitted' }
    vi.mocked(apiService.submitOrder).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Set up initial state with session and review card
    act(() => {
      result.current.uploadDocument(mockFile('test.pdf'))
    })

    // Add review card to make submission possible
    const reviewCard = {
      id: 'review',
      title: 'Review',
      status: ProcessingStatus.COMPLETED,
      content: {
        order_data: {
          customer_info: { name: 'Test Customer' },
          line_items: [],
          order_totals: { total_amount: 100.00 }
        }
      },
      timestamp: new Date().toISOString(),
    }

    act(() => {
      // Simulate receiving review card via WebSocket
      result.current.cards.push(reviewCard)
    })

    const orderData = reviewCard.content.order_data

    act(() => {
      result.current.submitOrder(orderData)
    })

    expect(result.current.isSubmitting).toBe(true)

    await waitFor(() => {
      expect(result.current.isSubmitting).toBe(false)
    })

    // Should add processing card during submission
    expect(result.current.cards.some(card => card.id === 'submission')).toBe(true)
  })

  it('handles order submission error', async () => {
    const { apiService } = await import('../../services/api')
    vi.mocked(apiService.submitOrder).mockRejectedValue(new Error('Submission failed'))

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Set up state for submission
    act(() => {
      result.current.submitOrder({ customer_info: {}, line_items: [] })
    })

    await waitFor(() => {
      const submissionCard = result.current.cards.find(card => card.id === 'submission')
      expect(submissionCard?.status).toBe(ProcessingStatus.ERROR)
      expect(result.current.hasErrors).toBe(true)
    })
  })

  it('retries submission correctly', async () => {
    const { apiService } = await import('../../services/api')
    vi.mocked(apiService.submitOrder).mockResolvedValue({ order_id: 'ORD-123' })

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Add review card with order data
    const reviewCard = {
      id: 'review',
      title: 'Review',
      status: ProcessingStatus.COMPLETED,
      content: {
        order_data: {
          customer_info: { name: 'Test Customer' },
          line_items: [],
        }
      },
      timestamp: new Date().toISOString(),
    }

    act(() => {
      result.current.cards.push(reviewCard)
    })

    act(() => {
      result.current.retrySubmission()
    })

    await waitFor(() => {
      expect(apiService.submitOrder).toHaveBeenCalledWith(
        result.current.sessionId,
        reviewCard.content.order_data
      )
    })
  })

  it('resets session correctly', () => {
    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Set up some state
    act(() => {
      result.current.uploadDocument(mockFile('test.pdf'))
    })

    // Reset session
    act(() => {
      result.current.resetSession()
    })

    expect(result.current.sessionId).toBeNull()
    expect(result.current.cards).toEqual([])
    expect(result.current.isProcessing).toBe(false)
    expect(result.current.hasActiveSession).toBe(false)
  })

  it('downloads order data as JSON', () => {
    // Mock URL.createObjectURL and document methods
    const mockCreateObjectURL = vi.fn(() => 'mock-url')
    const mockRevokeObjectURL = vi.fn()
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = mockRevokeObjectURL

    const mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    }
    const mockCreateElement = vi.fn(() => mockLink)
    const mockAppendChild = vi.fn()
    const mockRemoveChild = vi.fn()
    
    Object.defineProperty(document, 'createElement', { value: mockCreateElement })
    Object.defineProperty(document.body, 'appendChild', { value: mockAppendChild })
    Object.defineProperty(document.body, 'removeChild', { value: mockRemoveChild })

    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Add review card
    const reviewCard = {
      id: 'review',
      title: 'Review',
      status: ProcessingStatus.COMPLETED,
      content: {
        order_data: { customer_info: { name: 'Test' }, line_items: [] }
      },
      timestamp: new Date().toISOString(),
    }

    act(() => {
      result.current.cards.push(reviewCard)
    })

    act(() => {
      result.current.downloadOrder()
    })

    expect(mockCreateElement).toHaveBeenCalledWith('a')
    expect(mockLink.download).toContain('.json')
    expect(mockLink.click).toHaveBeenCalled()
    expect(mockCreateObjectURL).toHaveBeenCalled()
    expect(mockRevokeObjectURL).toHaveBeenCalled()
  })

  it('calculates canSubmit correctly', () => {
    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    // Initially cannot submit
    expect(result.current.canSubmit).toBe(false)

    // Add session but no review card
    act(() => {
      result.current.uploadDocument(mockFile('test.pdf'))
    })
    expect(result.current.canSubmit).toBe(false)

    // Add review card
    const reviewCard = {
      id: 'review',
      title: 'Review',
      status: ProcessingStatus.COMPLETED,
      content: { order_data: {} },
      timestamp: new Date().toISOString(),
    }

    act(() => {
      result.current.cards.push(reviewCard)
    })

    expect(result.current.canSubmit).toBe(true)
  })

  it('detects errors correctly', () => {
    const { result } = renderHook(() => useOrderProcessing(), {
      wrapper: createWrapper(),
    })

    expect(result.current.hasErrors).toBe(false)

    // Add error card
    const errorCard = {
      id: 'error',
      title: 'Error',
      status: ProcessingStatus.ERROR,
      content: { error: 'Something went wrong' },
      timestamp: new Date().toISOString(),
    }

    act(() => {
      result.current.cards.push(errorCard)
    })

    expect(result.current.hasErrors).toBe(true)
  })
})