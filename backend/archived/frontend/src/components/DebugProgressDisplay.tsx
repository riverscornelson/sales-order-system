import React from 'react';
import { ProcessingCard, ProcessingStatus } from '../types/api';

interface DebugProgressDisplayProps {
  sessionId: string | null;
  cards: ProcessingCard[];
  isProcessing: boolean;
  isUploading: boolean;
  wsConnected: boolean;
  sessionStatus: any;
}

export const DebugProgressDisplay: React.FC<DebugProgressDisplayProps> = ({
  sessionId,
  cards,
  isProcessing,
  isUploading,
  wsConnected,
  sessionStatus
}) => {
  const getStatusColor = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return 'bg-green-100 text-green-800 border-green-200';
      case ProcessingStatus.PROCESSING:
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case ProcessingStatus.ERROR:
        return 'bg-red-100 text-red-800 border-red-200';
      case ProcessingStatus.PENDING:
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return '✅';
      case ProcessingStatus.PROCESSING:
        return '🔄';
      case ProcessingStatus.ERROR:
        return '❌';
      case ProcessingStatus.PENDING:
        return '⏳';
      default:
        return '⚪';
    }
  };

  return (
    <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
      {/* System Status */}
      <div className="bg-white p-4 rounded border">
        <h3 className="font-bold text-lg mb-3">🔧 System Status</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div>Session ID: <code className="bg-gray-100 px-2 py-1 rounded text-xs">{sessionId || 'None'}</code></div>
            <div>WebSocket: <span className={wsConnected ? 'text-green-600' : 'text-red-600'}>{wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</span></div>
          </div>
          <div className="space-y-2">
            <div>Is Processing: <span className={isProcessing ? 'text-blue-600' : 'text-gray-600'}>{isProcessing ? '🔄 Yes' : '⏹️ No'}</span></div>
            <div>Is Uploading: <span className={isUploading ? 'text-blue-600' : 'text-gray-600'}>{isUploading ? '📤 Yes' : '⏹️ No'}</span></div>
          </div>
        </div>
      </div>

      {/* Session Status */}
      {sessionStatus && (
        <div className="bg-white p-4 rounded border">
          <h3 className="font-bold text-lg mb-3">📊 Session Data</h3>
          <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
            {JSON.stringify(sessionStatus, null, 2)}
          </pre>
        </div>
      )}

      {/* Processing Cards */}
      <div className="bg-white p-4 rounded border">
        <h3 className="font-bold text-lg mb-3">📋 Processing Steps ({cards.length})</h3>
        
        {cards.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No processing steps yet. Upload a file to begin.
          </div>
        ) : (
          <div className="space-y-3">
            {cards.map((card, index) => (
              <div
                key={card.id}
                className={`border rounded-lg p-4 ${getStatusColor(card.status)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{getStatusIcon(card.status)}</span>
                      <span className="font-semibold">{card.title}</span>
                      <span className="text-xs bg-white px-2 py-1 rounded">{card.status}</span>
                    </div>
                    
                    {card.content && (
                      <div className="space-y-2">
                        {typeof card.content === 'string' ? (
                          <div className="text-sm">{card.content}</div>
                        ) : (
                          <>
                            {card.content.message && (
                              <div className="text-sm font-medium">{card.content.message}</div>
                            )}
                            {card.content.status && (
                              <div className="text-xs">Status: {card.content.status}</div>
                            )}
                            {card.content.error && (
                              <div className="text-sm text-red-700 bg-red-50 p-2 rounded">
                                Error: {card.content.error}
                              </div>
                            )}
                            {card.content.details && (
                              <details className="text-xs">
                                <summary className="cursor-pointer">Show Details</summary>
                                <pre className="mt-2 bg-white p-2 rounded overflow-x-auto">
                                  {JSON.stringify(card.content.details, null, 2)}
                                </pre>
                              </details>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                  
                  <div className="text-xs text-gray-500 ml-4">
                    Step {index + 1}
                    {card.timestamp && (
                      <div>{new Date(card.timestamp).toLocaleTimeString()}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Current Activity */}
      <div className="bg-white p-4 rounded border">
        <h3 className="font-bold text-lg mb-3">⚡ Current Activity</h3>
        
        {isUploading && (
          <div className="flex items-center gap-2 text-blue-600">
            <div className="animate-spin">🔄</div>
            <span>Uploading file...</span>
          </div>
        )}
        
        {isProcessing && !isUploading && (
          <div className="flex items-center gap-2 text-blue-600">
            <div className="animate-pulse">🤖</div>
            <span>AI agents are processing your document...</span>
          </div>
        )}
        
        {!isProcessing && !isUploading && cards.length > 0 && (
          <div className="flex items-center gap-2 text-green-600">
            <span>✅</span>
            <span>Processing complete</span>
          </div>
        )}
        
        {!isProcessing && !isUploading && cards.length === 0 && (
          <div className="flex items-center gap-2 text-gray-500">
            <span>💤</span>
            <span>Waiting for file upload</span>
          </div>
        )}
      </div>

      {/* WebSocket Debug */}
      <div className="bg-white p-4 rounded border">
        <h3 className="font-bold text-lg mb-3">🔌 WebSocket Debug</h3>
        <div className="text-sm space-y-1">
          <div>URL: <code className="bg-gray-100 px-2 py-1 rounded text-xs">ws://localhost:8000/ws/client-{sessionId || 'none'}</code></div>
          <div>Status: {wsConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
          <div>Last Update: {cards.length > 0 ? new Date(cards[cards.length - 1].timestamp || '').toLocaleString() : 'None'}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-4 rounded border">
        <h3 className="font-bold text-lg mb-3">⚡ Quick Actions</h3>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => window.location.reload()}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
          >
            🔄 Refresh Page
          </button>
          
          {sessionId && (
            <button
              onClick={() => {
                fetch(`http://localhost:8000/api/v1/sessions/${sessionId}`)
                  .then(r => r.json())
                  .then(data => console.log('Session data:', data))
                  .catch(e => console.error('Session fetch error:', e));
              }}
              className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
            >
              📊 Check Session API
            </button>
          )}
          
          <button
            onClick={() => {
              console.log('Frontend Debug Info:', {
                sessionId,
                cards,
                isProcessing,
                isUploading,
                wsConnected,
                sessionStatus
              });
            }}
            className="px-3 py-1 bg-purple-500 text-white rounded text-sm hover:bg-purple-600"
          >
            🐛 Log Debug Info
          </button>
        </div>
      </div>
    </div>
  );
};