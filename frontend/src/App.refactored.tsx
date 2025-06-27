import React, { useState, useCallback, useMemo, memo } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { BackendStatus } from './components/BackendStatus';
import { FileUpload } from './components/FileUpload';
import { ProcessingStatus } from './components/ProcessingStatus';
import { useWebSocket } from './hooks/useWebSocket';
import { apiService } from './services/api';
import { ProcessingCard, WebSocketMessage } from './types';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [clientId, setClientId] = useState<string | null>(null);
  const [processingCards, setProcessingCards] = useState<ProcessingCard[]>([]);

  // WebSocket URL - only set when we have a clientId
  const wsUrl = useMemo(() => 
    clientId ? apiService.getWebSocketUrl(clientId) : null,
    [clientId]
  );

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    console.log('📨 WebSocket message:', message);
    
    const timestamp = new Date().toISOString();
    
    switch (message.type) {
      case 'status_update':
        setProcessingCards(prev => {
          const existingIndex = prev.findIndex(card => card.id === message.data.step);
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = { 
              ...updated[existingIndex], 
              status: message.data.status 
            };
            return updated;
          }
          return prev;
        });
        break;
        
      case 'agent_update':
        if (message.data && message.data.id) {
          setProcessingCards(prev => {
            const existingIndex = prev.findIndex(card => card.id === message.data.id);
            if (existingIndex >= 0) {
              const updated = [...prev];
              updated[existingIndex] = message.data;
              return updated;
            } else {
              return [...prev, message.data];
            }
          });
        }
        break;
        
      case 'final_results':
        setProcessingCards(prev => {
          const updated = [...prev];
          updated.push({
            id: 'final_results',
            title: '🎉 Order Processing Complete',
            status: 'completed',
            content: message.data,
            timestamp
          });
          return updated;
        });
        break;
        
      case 'error':
        setProcessingCards(prev => [...prev, {
          id: `error_${Date.now()}`,
          title: '❌ Error',
          status: 'error',
          content: message.data,
          timestamp
        }]);
        break;
    }
  }, []);

  // WebSocket event handlers
  const handleWebSocketOpen = useCallback(() => {
    const wsCard: ProcessingCard = {
      id: 'websocket',
      title: '🔌 WebSocket Connection',
      status: 'completed',
      content: { message: 'Real-time updates enabled', client_id: clientId },
      timestamp: new Date().toISOString()
    };
    setProcessingCards(prev => [...prev, wsCard]);
  }, [clientId]);

  // Use WebSocket hook
  const { isConnected: wsConnected } = useWebSocket(wsUrl, {
    onMessage: handleWebSocketMessage,
    onOpen: handleWebSocketOpen
  });

  // Memoized styles to prevent re-creation
  const containerStyle = useMemo(() => ({
    padding: '20px',
    backgroundColor: '#f9fafb',
    minHeight: '100vh',
    fontFamily: 'Arial, sans-serif'
  }), []);

  const maxWidthStyle = useMemo(() => ({
    maxWidth: '1200px',
    margin: '0 auto',
    paddingTop: '40px'
  }), []);

  const headingStyle = useMemo(() => ({
    textAlign: 'center' as const,
    marginBottom: '40px',
    fontSize: '32px',
    fontWeight: 700,
    color: '#111827'
  }), []);

  // Handle file upload
  const handleFileSelect = useCallback(async (file: File) => {
    console.log('🚀 FILE UPLOAD STARTED:', file.name);
    setSelectedFile(file);
    setUploading(true);
    setProcessingCards([]);
    
    try {
      const result = await apiService.uploadFile(file);
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
      
    } catch (error) {
      console.error('❌ Upload error:', error);
      setUploading(false);
      
      const errorCard: ProcessingCard = {
        id: 'upload_error',
        title: '❌ Upload Failed',
        status: 'error',
        content: error instanceof Error ? error.message : 'Unknown error occurred',
        timestamp: new Date().toISOString()
      };
      setProcessingCards([errorCard]);
    }
  }, []);

  // Memoized reset function
  const resetSession = useCallback(() => {
    setSelectedFile(null);
    setSessionId(null);
    setClientId(null);
    setProcessingCards([]);
  }, []);

  // Fetch session results
  const fetchSessionResults = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const data = await apiService.getSession(sessionId);
      console.log('📊 Session data:', data);
      
      if (data.results) {
        setProcessingCards(prev => [...prev, {
          id: 'fetched_results',
          title: '📊 Session Results',
          status: 'completed',
          content: data.results,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Failed to fetch session:', error);
    }
  }, [sessionId]);

  return (
    <ErrorBoundary>
      <div style={containerStyle}>
        <BackendStatus />
        
        <div style={maxWidthStyle}>
          <h1 style={headingStyle}>
            📋 Sales Order Entry System
          </h1>

          {!selectedFile && (
            <FileUpload 
              onFileSelect={handleFileSelect}
              disabled={uploading}
            />
          )}

          {selectedFile && (
            <>
              <div style={{ 
                textAlign: 'center', 
                marginBottom: '20px',
                color: '#6b7280',
                fontSize: '14px'
              }}>
                <strong>Selected file:</strong> {selectedFile.name} 
                ({(selectedFile.size / 1024).toFixed(1)} KB)
                {wsConnected && (
                  <span style={{ marginLeft: '10px', color: '#10b981' }}>
                    • 🟢 Connected
                  </span>
                )}
              </div>

              <ProcessingStatus 
                cards={processingCards}
                sessionId={sessionId}
              />

              {sessionId && processingCards.length > 0 && (
                <div style={{ 
                  textAlign: 'center', 
                  marginTop: '30px' 
                }}>
                  <button
                    onClick={fetchSessionResults}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500,
                      marginRight: '10px'
                    }}
                  >
                    🔄 Fetch Results
                  </button>
                  <button
                    onClick={resetSession}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500
                    }}
                  >
                    🆕 New Upload
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}</style>
      </div>
    </ErrorBoundary>
  );
}

export default App;