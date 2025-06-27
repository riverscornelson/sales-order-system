// This file has been refactored for better maintainability
// The monolithic 572-line component has been split into:
// - Separate components in components/ directory
// - Custom hooks for WebSocket handling
// - Service layer for API calls
// - Proper TypeScript types
// - Error boundaries for better error handling

// Import the refactored version
import App from './App.refactored';

export default App;

// Original implementation preserved below for reference
// TO BE REMOVED after testing

/*
import React, { useState, useCallback, useEffect, useRef } from 'react';

interface ProcessingCard {
  id: string;
  title: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  content?: any;
  timestamp?: string;
}

function AppLegacy() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [clientId, setClientId] = useState<string | null>(null);
  const [processingCards, setProcessingCards] = useState<ProcessingCard[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsMessages, setWsMessages] = useState<any[]>([]);
  const [backendStatus, setBackendStatus] = useState<string>('Unknown');
  const wsRef = useRef<WebSocket | null>(null);

  // Check backend status on load
  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      const health = await response.json();
      setBackendStatus(`✅ ${health.status} (${health.timestamp})`);
    } catch (error) {
      setBackendStatus(`❌ Disconnected: ${error}`);
    }
  };

  const handleFileSelect = async (file: File) => {
    console.log('🚀 FILE UPLOAD STARTED:', file.name);
    setSelectedFile(file);
    setUploading(true);
    setProcessingCards([]);
    setWsMessages([]);
    
    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('📤 Sending upload request...');
      const response = await fetch('http://localhost:8000/api/v1/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('✅ Upload response:', result);
      
      setSessionId(result.session_id);
      setClientId(result.client_id);
      setUploading(false);
      
      // Add upload success card
      const uploadCard: ProcessingCard = {
        id: 'upload',
        title: '📤 Document Upload',
        status: 'completed',
        content: { 
          filename: file.name, 
          size: `${(file.size / 1024).toFixed(1)} KB`,
          session_id: result.session_id
        },
        timestamp: new Date().toISOString()
      };
      setProcessingCards([uploadCard]);
      
      // Connect WebSocket
      console.log('🔌 Connecting WebSocket...');
      const ws = new WebSocket(`ws://localhost:8000/ws/${result.client_id}`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('✅ WebSocket CONNECTED');
        setWsConnected(true);
        
        // Add WebSocket connected card
        const wsCard: ProcessingCard = {
          id: 'websocket',
          title: '🔌 WebSocket Connection',
          status: 'completed',
          content: { message: 'Real-time updates enabled', client_id: result.client_id },
          timestamp: new Date().toISOString()
        };
        setProcessingCards(prev => [...prev, wsCard]);
      };
      
      ws.onmessage = (event) => {
        const timestamp = new Date().toISOString();
        console.log(`📨 [${timestamp}] WebSocket message:`, event.data);
        
        // Add to message log
        setWsMessages(prev => [...prev, { 
          timestamp, 
          data: event.data,
          parsed: null,
          error: null
        }]);
        
        try {
          const message = JSON.parse(event.data);
          console.log('📦 Parsed message:', message);
          
          // Update message log with parsed data
          setWsMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].parsed = message;
            return updated;
          });
          
          if (message.type === 'card_update') {
            console.log('🎯 Card update for:', message.data.id);
            
            setProcessingCards(prev => {
              const existingIndex = prev.findIndex(card => card.id === message.data.id);
              if (existingIndex !== -1) {
                const updated = [...prev];
                updated[existingIndex] = { ...message.data };
                return updated;
              } else {
                return [...prev, message.data];
              }
            });
          }
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
          setWsMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].error = error.toString();
            return updated;
          });
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setWsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setWsConnected(false);
      };
      
    } catch (error) {
      console.error('❌ Upload error:', error);
      setUploading(false);
      
      const errorCard: ProcessingCard = {
        id: 'upload-error',
        title: '❌ Upload Error',
        status: 'error',
        content: { error: error.toString() },
        timestamp: new Date().toISOString()
      };
      setProcessingCards([errorCard]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

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
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'processing': return '🔄';
      case 'error': return '❌';
      case 'pending': return '⏳';
      default: return '⚪';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return { bg: '#dcfce7', text: '#166534' };
      case 'processing': return { bg: '#fef3c7', text: '#92400e' };
      case 'error': return { bg: '#fee2e2', text: '#dc2626' };
      case 'pending': return { bg: '#f3f4f6', text: '#374151' };
      default: return { bg: '#f3f4f6', text: '#374151' };
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f9fafb', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px'
      }}>
        
        {/* Left Column - Upload and Processing */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          height: 'fit-content'
        }}>
          <h1 style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: '#111827',
            marginBottom: '20px'
          }}>
            🚀 Sales Order System
          </h1>
          
          {/* System Status */}
          <div style={{
            padding: '15px',
            backgroundColor: '#f9fafb',
            borderRadius: '6px',
            marginBottom: '20px',
            fontSize: '0.9rem'
          }}>
            <div><strong>Backend:</strong> {backendStatus}</div>
            <div><strong>WebSocket:</strong> {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
            <div><strong>Session:</strong> {sessionId ? `✅ ${sessionId.slice(0, 8)}...` : '❌ None'}</div>
            <div><strong>Processing:</strong> {uploading ? '📤 Uploading' : processingCards.length > 1 ? '🤖 Active' : '💤 Idle'}</div>
          </div>
          
          {/* Upload Area */}
          <div 
            style={{
              border: `2px dashed ${dragActive ? '#3b82f6' : '#d1d5db'}`,
              borderRadius: '8px',
              padding: '40px',
              textAlign: 'center',
              backgroundColor: dragActive ? '#eff6ff' : '#f9fafb',
              cursor: 'pointer',
              marginBottom: '20px'
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('fileInput')?.click()}
          >
            <input
              id="fileInput"
              type="file"
              accept=".pdf,.eml,.msg,.txt"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            
            {uploading ? (
              <div>
                <div style={{ fontSize: '1.2rem', color: '#3b82f6', marginBottom: '10px' }}>
                  🔄 Uploading...
                </div>
                <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                  Please wait while we process your file
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
                  {dragActive ? '📂 Drop it here!' : '📄 Drop your order document here'}
                </div>
                <div style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                  or click to browse files
                </div>
              </div>
            )}
          </div>
          
          {/* Quick Actions */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={checkBackendStatus}
              style={{
                padding: '8px 16px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              🔄 Check Backend
            </button>
            
            {sessionId && (
              <button 
                onClick={async () => {
                  try {
                    const response = await fetch(`http://localhost:8000/api/v1/sessions/${sessionId}`);
                    const data = await response.json();
                    console.log('Session data:', data);
                    alert('Session data logged to console');
                  } catch (error) {
                    alert(`Session check failed: ${error}`);
                  }
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                📊 Check Session
              </button>
            )}
            
            <button 
              onClick={() => {
                setProcessingCards([]);
                setWsMessages([]);
                setSessionId(null);
                setClientId(null);
                setSelectedFile(null);
                if (wsRef.current) {
                  wsRef.current.close();
                }
              }}
              style={{
                padding: '8px 16px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              🗑️ Reset
            </button>
          </div>
        </div>
        
        {/* Right Column - Debug Information */}
        <div style={{
          backgroundColor: 'white',
          padding: '30px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          height: 'fit-content'
        }}>
          <h2 style={{ 
            fontSize: '1.25rem', 
            fontWeight: 'bold', 
            color: '#111827',
            marginBottom: '20px'
          }}>
            🔍 Processing Pipeline
          </h2>
          
          {/* Processing Cards */}
          {processingCards.length > 0 ? (
            <div style={{ marginBottom: '30px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '15px' }}>
                📋 Steps ({processingCards.length})
              </h3>
              {processingCards.map((card, index) => {
                const colors = getStatusColor(card.status);
                return (
                  <div 
                    key={`${card.id}-${index}`}
                    style={{
                      marginBottom: '10px',
                      padding: '15px',
                      backgroundColor: colors.bg,
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px'
                    }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      marginBottom: '8px'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '1.2rem' }}>{getStatusIcon(card.status)}</span>
                        <span style={{ fontWeight: '500', color: colors.text }}>
                          {card.title}
                        </span>
                      </div>
                      <span style={{
                        padding: '2px 8px',
                        backgroundColor: 'white',
                        color: colors.text,
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: '500'
                      }}>
                        {card.status}
                      </span>
                    </div>
                    
                    {card.content && (
                      <div style={{ 
                        fontSize: '0.85rem', 
                        color: '#6b7280',
                        backgroundColor: 'white',
                        padding: '8px',
                        borderRadius: '4px',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '100px',
                        overflow: 'auto'
                      }}>
                        {typeof card.content === 'string' 
                          ? card.content 
                          : JSON.stringify(card.content, null, 2)
                        }
                      </div>
                    )}
                    
                    {card.timestamp && (
                      <div style={{ 
                        fontSize: '0.7rem', 
                        color: '#9ca3af',
                        marginTop: '5px'
                      }}>
                        {new Date(card.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ 
              textAlign: 'center', 
              color: '#6b7280', 
              padding: '20px',
              backgroundColor: '#f9fafb',
              borderRadius: '6px',
              marginBottom: '30px'
            }}>
              No processing steps yet. Upload a file to begin.
            </div>
          )}
          
          {/* WebSocket Messages */}
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '15px' }}>
              📡 WebSocket Messages ({wsMessages.length})
            </h3>
            
            {wsMessages.length > 0 ? (
              <div style={{ 
                maxHeight: '300px', 
                overflow: 'auto',
                backgroundColor: '#f9fafb',
                border: '1px solid #e5e7eb',
                borderRadius: '6px'
              }}>
                {wsMessages.slice(-10).map((msg, index) => (
                  <div 
                    key={index}
                    style={{
                      padding: '10px',
                      borderBottom: index < wsMessages.length - 1 ? '1px solid #e5e7eb' : 'none'
                    }}
                  >
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: '#6b7280',
                      marginBottom: '5px'
                    }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                    
                    {msg.parsed ? (
                      <div style={{ 
                        fontSize: '0.8rem',
                        fontFamily: 'monospace',
                        backgroundColor: 'white',
                        padding: '8px',
                        borderRadius: '4px',
                        border: '1px solid #d1d5db'
                      }}>
                        <div style={{ color: '#059669', fontWeight: '500' }}>
                          Type: {msg.parsed.type}
                        </div>
                        {msg.parsed.data && (
                          <div style={{ marginTop: '4px', color: '#374151' }}>
                            {JSON.stringify(msg.parsed.data, null, 2)}
                          </div>
                        )}
                      </div>
                    ) : msg.error ? (
                      <div style={{ 
                        fontSize: '0.8rem',
                        color: '#dc2626',
                        backgroundColor: '#fee2e2',
                        padding: '8px',
                        borderRadius: '4px'
                      }}>
                        Error: {msg.error}
                      </div>
                    ) : (
                      <div style={{ 
                        fontSize: '0.8rem',
                        fontFamily: 'monospace',
                        color: '#6b7280'
                      }}>
                        {msg.data}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                color: '#6b7280', 
                padding: '15px',
                backgroundColor: '#f9fafb',
                borderRadius: '6px'
              }}>
                No WebSocket messages yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AppLegacy;
*/