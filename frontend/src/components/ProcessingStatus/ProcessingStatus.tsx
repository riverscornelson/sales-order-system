import { memo, useMemo } from 'react';
import type { ProcessingCard as ProcessingCardType } from '../../types';
import { ProcessingCard } from './ProcessingCard';

interface ProcessingStatusProps {
  cards: ProcessingCardType[];
  sessionId: string | null;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = memo(({ 
  cards, 
  sessionId 
}) => {
  if (cards.length === 0) {
    return null;
  }

  return (
    <div style={{
      marginTop: '40px',
      maxWidth: '800px',
      margin: '40px auto 0'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px'
      }}>
        <h2 style={{
          fontSize: '24px',
          fontWeight: 600,
          color: '#111827',
          margin: 0
        }}>
          Processing Status
        </h2>
        {sessionId && (
          <span style={{
            fontSize: '12px',
            color: '#6b7280',
            fontFamily: 'monospace',
            backgroundColor: '#f3f4f6',
            padding: '4px 8px',
            borderRadius: '4px'
          }}>
            Session: {sessionId}
          </span>
        )}
      </div>
      
      <div>
        {useMemo(() => 
          cards.map((card) => (
            <ProcessingCard key={card.id} card={card} />
          )), [cards]
        )}
      </div>
    </div>
  );
});