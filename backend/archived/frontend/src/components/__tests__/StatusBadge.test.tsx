import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../StatusBadge'
import { ProcessingStatus } from '../../types/api'

describe('StatusBadge', () => {
  it('renders completed status correctly', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} />)
    
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Completed').closest('div')).toHaveClass('bg-green-50', 'text-green-800')
  })

  it('renders error status correctly', () => {
    render(<StatusBadge status={ProcessingStatus.ERROR} />)
    
    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('Error').closest('div')).toHaveClass('bg-red-50', 'text-red-800')
  })

  it('renders processing status correctly', () => {
    render(<StatusBadge status={ProcessingStatus.PROCESSING} />)
    
    expect(screen.getByText('Processing')).toBeInTheDocument()
    expect(screen.getByText('Processing').closest('div')).toHaveClass('bg-blue-50', 'text-blue-800')
  })

  it('renders pending status correctly', () => {
    render(<StatusBadge status={ProcessingStatus.PENDING} />)
    
    expect(screen.getByText('Pending')).toBeInTheDocument()
    expect(screen.getByText('Pending').closest('div')).toHaveClass('bg-yellow-50', 'text-yellow-800')
  })

  it('renders without icon when showIcon is false', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} showIcon={false} />)
    
    expect(screen.getByText('Completed')).toBeInTheDocument()
    // Icon should not be present
    expect(screen.queryByTestId('status-icon')).not.toBeInTheDocument()
  })

  it('renders without text when showText is false', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} showText={false} />)
    
    expect(screen.queryByText('Completed')).not.toBeInTheDocument()
    // Icon should still be present
    expect(screen.getByTestId('status-icon') || screen.getByRole('img')).toBeInTheDocument()
  })

  it('renders with small size', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} size="sm" />)
    
    const badge = screen.getByText('Completed').closest('div')
    expect(badge).toHaveClass('px-2', 'py-1', 'text-xs')
  })

  it('renders with large size', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} size="lg" />)
    
    const badge = screen.getByText('Completed').closest('div')
    expect(badge).toHaveClass('px-4', 'py-2', 'text-base')
  })

  it('renders with medium size by default', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} />)
    
    const badge = screen.getByText('Completed').closest('div')
    expect(badge).toHaveClass('px-3', 'py-1', 'text-sm')
  })

  it('shows animated loader for processing status', () => {
    render(<StatusBadge status={ProcessingStatus.PROCESSING} animated={true} />)
    
    // Should show animated loader icon
    const badge = screen.getByText('Processing').closest('div')
    expect(badge).toBeInTheDocument()
  })

  it('does not animate when animated is false', () => {
    render(<StatusBadge status={ProcessingStatus.PROCESSING} animated={false} />)
    
    // Should show static icon instead of animated loader
    const badge = screen.getByText('Processing').closest('div')
    expect(badge).toBeInTheDocument()
  })

  it('applies correct icon colors', () => {
    const { rerender } = render(<StatusBadge status={ProcessingStatus.COMPLETED} />)
    
    // Check completed icon color
    let icon = screen.getByText('Completed').previousElementSibling
    expect(icon).toHaveClass('text-green-600')
    
    // Check error icon color
    rerender(<StatusBadge status={ProcessingStatus.ERROR} />)
    icon = screen.getByText('Error').previousElementSibling
    expect(icon).toHaveClass('text-red-600')
    
    // Check processing icon color
    rerender(<StatusBadge status={ProcessingStatus.PROCESSING} />)
    icon = screen.getByText('Processing').previousElementSibling
    expect(icon).toHaveClass('text-blue-600')
    
    // Check pending icon color
    rerender(<StatusBadge status={ProcessingStatus.PENDING} />)
    icon = screen.getByText('Pending').previousElementSibling
    expect(icon).toHaveClass('text-gray-600')
  })

  it('maintains accessibility with proper roles', () => {
    render(<StatusBadge status={ProcessingStatus.COMPLETED} />)
    
    const badge = screen.getByText('Completed').closest('div')
    expect(badge).toHaveAttribute('role', 'status')
  })
})