import { useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiService } from '../services/api';
import { useWebSocket } from './useWebSocket';
import { ProcessingCard, ProcessingStatus, WebSocketMessage } from '../types/api';

export const useOrderProcessing = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cards, setCards] = useState<ProcessingCard[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Generate client ID for WebSocket connection
  const clientId = `client-${Date.now()}`;

  // WebSocket connection for real-time updates
  const { subscribeToSession } = useWebSocket(clientId, {
    onMessage: handleWebSocketMessage,
    onConnect: () => console.log('WebSocket connected'),
    onDisconnect: () => console.log('WebSocket disconnected'),
    onError: (error) => console.error('WebSocket error:', error)
  });

  function handleWebSocketMessage(message: WebSocketMessage) {
    if (message.type === 'card_update') {
      const newCard = message.data as ProcessingCard;
      setCards(prev => {
        const existing = prev.find(card => card.id === newCard.id);
        if (existing) {
          return prev.map(card => card.id === newCard.id ? newCard : card);
        } else {
          return [...prev, newCard];
        }
      });
    }
  }

  // Upload document mutation
  const uploadMutation = useMutation({
    mutationFn: apiService.uploadDocument,
    onSuccess: (response) => {
      setSessionId(response.session_id);
      setIsProcessing(true);
      
      // Subscribe to WebSocket updates for this session
      subscribeToSession(response.session_id, handleWebSocketMessage);
      
      // Add initial upload card
      const uploadCard: ProcessingCard = {
        id: 'upload',
        title: 'Document Upload',
        status: ProcessingStatus.COMPLETED,
        content: {
          session_id: response.session_id,
          status: 'uploaded',
          message: response.message
        },
        timestamp: new Date().toISOString()
      };
      
      setCards([uploadCard]);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      
      const errorCard: ProcessingCard = {
        id: 'upload-error',
        title: 'Upload Error',
        status: ProcessingStatus.ERROR,
        content: {
          error: 'Failed to upload document. Please try again.'
        },
        timestamp: new Date().toISOString()
      };
      
      setCards([errorCard]);
    }
  });

  // Submit order mutation
  const submitOrderMutation = useMutation({
    mutationFn: ({ sessionId, orderData }: { sessionId: string; orderData: any }) =>
      apiService.submitOrder(sessionId, orderData),
    onMutate: () => {
      // Add processing card immediately
      const processingCard: ProcessingCard = {
        id: 'submission',
        title: 'Order Submission',
        status: ProcessingStatus.PROCESSING,
        content: {
          status: 'submitting',
          message: 'Submitting order to ERP system...'
        },
        timestamp: new Date().toISOString()
      };
      
      setCards(prev => [...prev, processingCard]);
    },
    onSuccess: (response, variables) => {
      const successCard: ProcessingCard = {
        id: 'submission',
        title: 'Order Submission',
        status: ProcessingStatus.COMPLETED,
        content: {
          status: 'submitted',
          order_id: response.order_id,
          message: 'Order submitted successfully',
          total_amount: variables.orderData.order_totals?.total_amount
        },
        timestamp: new Date().toISOString()
      };
      
      setCards(prev => prev.map(card => 
        card.id === 'submission' ? successCard : card
      ));
      
      setIsProcessing(false);
    },
    onError: (error) => {
      console.error('Order submission failed:', error);
      
      const errorCard: ProcessingCard = {
        id: 'submission',
        title: 'Order Submission',
        status: ProcessingStatus.ERROR,
        content: {
          status: 'failed',
          error: 'Failed to submit order. Please try again.',
          retry_count: 0,
          max_retries: 3
        },
        timestamp: new Date().toISOString()
      };
      
      setCards(prev => prev.map(card => 
        card.id === 'submission' ? errorCard : card
      ));
    }
  });

  // Session status query
  const { data: sessionStatus } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => sessionId ? apiService.getSessionStatus(sessionId) : null,
    enabled: !!sessionId,
    refetchInterval: 5000, // Poll every 5 seconds
    refetchIntervalInBackground: false
  });

  const uploadDocument = useCallback((file: File) => {
    setCards([]); // Clear previous cards
    setIsProcessing(true);
    uploadMutation.mutate(file);
  }, [uploadMutation]);

  const submitOrder = useCallback((orderData: any) => {
    if (!sessionId) return;
    
    submitOrderMutation.mutate({ sessionId, orderData });
  }, [sessionId, submitOrderMutation]);

  const retrySubmission = useCallback(() => {
    const reviewCard = cards.find(card => card.id === 'review');
    if (reviewCard && sessionId) {
      const orderData = reviewCard.content.order_data;
      submitOrderMutation.mutate({ sessionId, orderData });
    }
  }, [cards, sessionId, submitOrderMutation]);

  const resetSession = useCallback(() => {
    setSessionId(null);
    setCards([]);
    setIsProcessing(false);
    uploadMutation.reset();
    submitOrderMutation.reset();
  }, [uploadMutation, submitOrderMutation]);

  const downloadOrder = useCallback(() => {
    const reviewCard = cards.find(card => card.id === 'review');
    if (!reviewCard) return;

    const orderData = reviewCard.content.order_data;
    const dataStr = JSON.stringify(orderData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `order-${sessionId || 'unknown'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [cards, sessionId]);

  return {
    // State
    sessionId,
    cards,
    isProcessing,
    isUploading: uploadMutation.isPending,
    isSubmitting: submitOrderMutation.isPending,
    sessionStatus,
    
    // Actions
    uploadDocument,
    submitOrder,
    retrySubmission,
    resetSession,
    downloadOrder,
    
    // Computed values
    hasActiveSession: !!sessionId,
    canSubmit: sessionId && !isProcessing && cards.some(card => card.id === 'review'),
    hasErrors: cards.some(card => card.status === ProcessingStatus.ERROR)
  };
};