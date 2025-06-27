import { memo } from 'react';
import type { ProcessingCard as ProcessingCardType } from '../../types';

interface ProcessingCardProps {
  card: ProcessingCardType;
}

export const ProcessingCard: React.FC<ProcessingCardProps> = memo(({ card }) => {
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

  const colors = getStatusColor(card.status);

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '20px',
      marginBottom: '15px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      border: '1px solid #e5e7eb',
      animation: card.status === 'processing' ? 'pulse 2s infinite' : 'none'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '10px'
      }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '16px',
          fontWeight: 600,
          color: '#111827'
        }}>
          {card.title}
        </h3>
        <span style={{
          padding: '4px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 500,
          backgroundColor: colors.bg,
          color: colors.text,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <span>{getStatusIcon(card.status)}</span>
          <span>{card.status.charAt(0).toUpperCase() + card.status.slice(1)}</span>
        </span>
      </div>
      
      {card.content && (
        <div style={{ 
          marginTop: '10px',
          padding: '12px',
          backgroundColor: '#f9fafb',
          borderRadius: '6px',
          fontSize: '14px',
          lineHeight: '1.5'
        }}>
          <pre style={{ 
            margin: 0, 
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {typeof card.content === 'string' 
              ? card.content 
              : JSON.stringify(card.content, null, 2)}
          </pre>
        </div>
      )}
      
      {card.timestamp && (
        <div style={{
          marginTop: '10px',
          fontSize: '12px',
          color: '#6b7280'
        }}>
          {new Date(card.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
});