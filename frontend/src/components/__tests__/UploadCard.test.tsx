import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UploadCard } from '../UploadCard'
import { mockFile } from '../../test/setup'

describe('UploadCard', () => {
  const defaultProps = {
    onFileUpload: vi.fn(),
    isUploading: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload interface correctly', () => {
    render(<UploadCard {...defaultProps} />)
    
    expect(screen.getByText('Upload Document')).toBeInTheDocument()
    expect(screen.getByText('Drop your order document here')).toBeInTheDocument()
    expect(screen.getByText('or click to browse files')).toBeInTheDocument()
    expect(screen.getByText('PDF')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
  })

  it('handles file selection through input', async () => {
    const user = userEvent.setup()
    render(<UploadCard {...defaultProps} />)
    
    const file = mockFile('test.pdf', 'application/pdf')
    const input = screen.getByRole('button', { hidden: true }) // File input is hidden
    
    await user.upload(input, file)
    
    expect(defaultProps.onFileUpload).toHaveBeenCalledWith(file)
  })

  it('handles drag and drop', async () => {
    render(<UploadCard {...defaultProps} />)
    
    const file = mockFile('test.pdf', 'application/pdf')
    const dropZone = screen.getByText('Drop your order document here').closest('div')
    
    // Simulate drag enter
    fireEvent.dragEnter(dropZone!, { dataTransfer: { files: [file] } })
    expect(screen.getByText('Drop it like it\'s hot!')).toBeInTheDocument()
    
    // Simulate drop
    fireEvent.drop(dropZone!, { dataTransfer: { files: [file] } })
    
    expect(defaultProps.onFileUpload).toHaveBeenCalledWith(file)
  })

  it('shows uploading state correctly', () => {
    render(<UploadCard {...defaultProps} isUploading={true} />)
    
    expect(screen.getByText('Uploading Document...')).toBeInTheDocument()
    expect(screen.getByText('Please wait while we process your file')).toBeInTheDocument()
  })

  it('disables interaction during upload', () => {
    render(<UploadCard {...defaultProps} isUploading={true} />)
    
    const dropZone = screen.getByText('Uploading Document...').closest('div')
    expect(dropZone).toHaveClass('pointer-events-none')
  })

  it('accepts correct file types', () => {
    render(<UploadCard {...defaultProps} />)
    
    const input = screen.getByRole('button', { hidden: true })
    expect(input).toHaveAttribute('accept', '.pdf,.eml,.msg,.txt')
  })

  it('shows drag active state', () => {
    render(<UploadCard {...defaultProps} />)
    
    const file = mockFile('test.pdf')
    const dropZone = screen.getByText('Drop your order document here').closest('div')
    
    fireEvent.dragEnter(dropZone!, { dataTransfer: { files: [file] } })
    
    expect(dropZone).toHaveClass('border-blue-500', 'bg-blue-50')
  })

  it('removes drag active state on drag leave', () => {
    render(<UploadCard {...defaultProps} />)
    
    const file = mockFile('test.pdf')
    const dropZone = screen.getByText('Drop your order document here').closest('div')
    
    fireEvent.dragEnter(dropZone!, { dataTransfer: { files: [file] } })
    fireEvent.dragLeave(dropZone!)
    
    expect(screen.getByText('Drop your order document here')).toBeInTheDocument()
  })

  it('prevents default drag behaviors', () => {
    render(<UploadCard {...defaultProps} />)
    
    const dropZone = screen.getByText('Drop your order document here').closest('div')
    const dragEvent = new Event('dragover')
    const preventDefaultSpy = vi.spyOn(dragEvent, 'preventDefault')
    
    fireEvent(dropZone!, dragEvent)
    
    expect(preventDefaultSpy).toHaveBeenCalled()
  })
})