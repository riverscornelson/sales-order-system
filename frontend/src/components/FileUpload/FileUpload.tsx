import React, { useState, useCallback, memo } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  acceptedTypes?: string[];
}

export const FileUpload: React.FC<FileUploadProps> = memo(({ 
  onFileSelect, 
  disabled = false,
  acceptedTypes = ['.pdf', '.txt', '.doc', '.docx', '.eml', '.msg']
}) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div 
      onDragEnter={handleDrag}
      style={{
        width: '100%',
        maxWidth: '600px',
        margin: '0 auto',
        opacity: disabled ? 0.5 : 1,
        pointerEvents: disabled ? 'none' : 'auto'
      }}
    >
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? '#3b82f6' : '#d1d5db'}`,
          borderRadius: '8px',
          padding: '60px 20px',
          textAlign: 'center',
          backgroundColor: dragActive ? '#eff6ff' : '#f9fafb',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>
          📄
        </div>
        <p style={{ 
          fontSize: '18px', 
          color: '#374151', 
          marginBottom: '10px',
          fontWeight: 500
        }}>
          {dragActive ? 'Drop your file here' : 'Drag and drop your sales order'}
        </p>
        <p style={{ 
          fontSize: '14px', 
          color: '#6b7280',
          marginBottom: '20px'
        }}>
          or
        </p>
        <label style={{
          display: 'inline-block',
          padding: '10px 20px',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '6px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: 500,
          transition: 'background-color 0.2s'
        }}>
          Browse Files
          <input
            type="file"
            onChange={handleFileChange}
            accept={acceptedTypes.join(',')}
            style={{ display: 'none' }}
            disabled={disabled}
          />
        </label>
        <p style={{ 
          fontSize: '12px', 
          color: '#9ca3af',
          marginTop: '20px'
        }}>
          Supported formats: PDF, TXT, DOC, DOCX, EML, MSG
        </p>
      </div>
    </div>
  );
});