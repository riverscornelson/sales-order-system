import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProcessingCard } from '../ProcessingCard'
import { ProcessingStatus, ConfidenceLevel } from '../../types/api'

describe('ProcessingCard', () => {
  const defaultProps = {
    title: 'Test Processing Card',
    status: ProcessingStatus.COMPLETED,
    content: {
      message: 'Processing completed successfully',
      details: 'Additional details',
      metadata: { confidence: 0.95 }
    },
    timestamp: '2024-01-15T10:30:00Z',
    confidence: ConfidenceLevel.HIGH,
  }

  it('renders card with basic information', () => {
    render(<ProcessingCard {...defaultProps} />)
    
    expect(screen.getByText('Test Processing Card')).toBeInTheDocument()
    expect(screen.getByText('Processing completed successfully')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('High Confidence')).toBeInTheDocument()
  })

  it('shows correct status icon for completed status', () => {
    render(<ProcessingCard {...defaultProps} />)
    
    // Check for CheckCircle icon (completed status)
    const icon = screen.getByText('Test Processing Card').previousElementSibling
    expect(icon).toHaveClass('text-green-600')
  })

  it('shows correct status icon for error status', () => {
    render(
      <ProcessingCard 
        {...defaultProps} 
        status={ProcessingStatus.ERROR}
      />
    )
    
    const icon = screen.getByText('Test Processing Card').previousElementSibling
    expect(icon).toHaveClass('text-red-600')
  })

  it('shows correct status icon for processing status', () => {
    render(
      <ProcessingCard 
        {...defaultProps} 
        status={ProcessingStatus.PROCESSING}
      />
    )
    
    const icon = screen.getByText('Test Processing Card').previousElementSibling
    expect(icon).toHaveClass('text-blue-600')
  })

  it('expands to show detailed content when clicked', () => {
    const contentWithDetails = {
      ...defaultProps.content,
      extra_field1: 'Extra data 1',
      extra_field2: 'Extra data 2',
      extra_field3: 'Extra data 3',
      extra_field4: 'Extra data 4',
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={contentWithDetails}
      />
    )
    
    // Should show essential content (first 3 items)
    expect(screen.getByText('message')).toBeInTheDocument()
    expect(screen.getByText('details')).toBeInTheDocument()
    expect(screen.getByText('metadata')).toBeInTheDocument()
    
    // Should not show detailed content initially
    expect(screen.queryByText('extra field1')).not.toBeInTheDocument()
    
    // Click to expand
    const header = screen.getByText('Test Processing Card').closest('div')
    fireEvent.click(header!)
    
    // Should now show detailed content
    expect(screen.getByText('extra field1')).toBeInTheDocument()
    expect(screen.getByText('extra field2')).toBeInTheDocument()
  })

  it('shows chevron down icon when expandable', () => {
    const contentWithManyFields = {
      field1: 'value1',
      field2: 'value2',
      field3: 'value3',
      field4: 'value4', // This will make it expandable
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={contentWithManyFields}
      />
    )
    
    // Should show chevron down icon
    expect(screen.getByText('Test Processing Card').parentElement).toContainHTML('ChevronDown')
  })

  it('does not show chevron when not expandable', () => {
    const simpleContent = {
      field1: 'value1',
      field2: 'value2',
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={simpleContent}
      />
    )
    
    // Should not show chevron
    expect(screen.queryByText('Test Processing Card').parentElement).not.toContainHTML('ChevronDown')
  })

  it('handles object values in content', () => {
    const contentWithObject = {
      simple_field: 'simple value',
      complex_field: { nested: 'value', array: [1, 2, 3] }
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={contentWithObject}
      />
    )
    
    // Should render JSON for complex objects
    expect(screen.getByText('simple value')).toBeInTheDocument()
    expect(screen.getByText(/"nested"/)).toBeInTheDocument()
  })

  it('shows raw data toggle when expanded', () => {
    const contentWithDetails = {
      field1: 'value1',
      field2: 'value2',
      field3: 'value3',
      field4: 'value4', // Makes it expandable
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={contentWithDetails}
      />
    )
    
    // Expand the card
    const header = screen.getByText('Test Processing Card').closest('div')
    fireEvent.click(header!)
    
    // Should show raw data toggle
    expect(screen.getByText('Show Raw Data')).toBeInTheDocument()
  })

  it('toggles raw data view', () => {
    const contentWithDetails = {
      field1: 'value1',
      field2: 'value2',
      field3: 'value3',
      field4: 'value4',
    }

    render(
      <ProcessingCard 
        {...defaultProps} 
        content={contentWithDetails}
      />
    )
    
    // Expand the card
    const header = screen.getByText('Test Processing Card').closest('div')
    fireEvent.click(header!)
    
    // Click raw data toggle
    const rawDataButton = screen.getByText('Show Raw Data')
    fireEvent.click(rawDataButton)
    
    // Should show raw JSON
    expect(screen.getByText('Hide Raw Data')).toBeInTheDocument()
  })

  it('formats timestamp correctly', () => {
    render(<ProcessingCard {...defaultProps} />)
    
    // Should show formatted timestamp
    const timestamp = new Date('2024-01-15T10:30:00Z').toLocaleString()
    expect(screen.getByText(timestamp)).toBeInTheDocument()
  })

  it('shows confidence badge when provided', () => {
    render(<ProcessingCard {...defaultProps} confidence={ConfidenceLevel.MEDIUM} />)
    
    expect(screen.getByText('Medium Confidence')).toBeInTheDocument()
  })

  it('does not show confidence badge when not provided', () => {
    render(<ProcessingCard {...defaultProps} confidence={undefined} />)
    
    expect(screen.queryByText(/Confidence/)).not.toBeInTheDocument()
  })

  it('applies correct CSS classes for different statuses', () => {
    const { rerender } = render(
      <ProcessingCard {...defaultProps} status={ProcessingStatus.COMPLETED} />
    )
    
    expect(screen.getByText('Completed')).toHaveClass('badge-green')
    
    rerender(<ProcessingCard {...defaultProps} status={ProcessingStatus.ERROR} />)
    expect(screen.getByText('Error')).toHaveClass('badge-red')
    
    rerender(<ProcessingCard {...defaultProps} status={ProcessingStatus.PROCESSING} />)
    expect(screen.getByText('Processing')).toHaveClass('badge-blue')
    
    rerender(<ProcessingCard {...defaultProps} status={ProcessingStatus.PENDING} />)
    expect(screen.getByText('Pending')).toHaveClass('badge-yellow')
  })
})