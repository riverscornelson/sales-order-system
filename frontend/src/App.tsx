import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCard } from './components/UploadCard';
import { ProcessingCard } from './components/ProcessingCard';
import { ExtractionCard } from './components/ExtractionCard';
import { MatchingCard } from './components/MatchingCard';
import { ERPValidationCard } from './components/ERPValidationCard';
import { ReviewCard } from './components/ReviewCard';
import { ActionCard } from './components/ActionCard';
import { useOrderProcessing } from './hooks/useOrderProcessing';
import { ProcessingStatus } from './types/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

function App() {
  const {
    sessionId,
    cards,
    isUploading,
    hasActiveSession,
    uploadDocument,
    submitOrder,
    retrySubmission,
    resetSession,
    downloadOrder
  } = useOrderProcessing();

  const handleFileUpload = (file: File) => {
    uploadDocument(file);
  };


  const handleSubmitOrder = () => {
    const reviewCard = cards.find(card => card.id === 'review');
    if (reviewCard && reviewCard.content.order_data) {
      submitOrder(reviewCard.content.order_data);
    }
  };

  const handleEditItem = (lineNumber: number) => {
    console.log('Edit item:', lineNumber);
    // TODO: Implement line item editing
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <motion.div 
            className="text-center mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          >
            <motion.h1 
              className="text-3xl font-bold text-gray-900 mb-2 glow"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400, damping: 10 }}
            >
              Sales Order Entry System
            </motion.h1>
            <motion.p 
              className="text-gray-600"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              Upload customer orders and let AI extract and process the information
            </motion.p>
          </motion.div>

          {/* Upload Section */}
          {!hasActiveSession && (
            <UploadCard 
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
            />
          )}

          {/* Processing Cards */}
          <AnimatePresence>
            {cards.length > 0 && (
              <motion.div 
                className="space-y-6 mt-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                {cards.map((card, index) => {
                  // Route to specialized card components based on card ID
                  const CardComponent = (() => {
                    switch (card.id) {
                      case 'extraction':
                        return (
                          <ExtractionCard
                            status={card.status}
                            data={card.content}
                            timestamp={card.timestamp}
                          />
                        );
                      case 'matching':
                        return (
                          <MatchingCard
                            status={card.status}
                            data={card.content}
                            timestamp={card.timestamp}
                          />
                        );
                      case 'erp_validation':
                        return (
                          <ERPValidationCard
                            status={card.status}
                            data={card.content}
                            timestamp={card.timestamp}
                          />
                        );
                      case 'review':
                        return (
                          <ReviewCard
                            status={card.status}
                            data={card.content}
                            timestamp={card.timestamp}
                            onSubmitOrder={handleSubmitOrder}
                            onEditItem={handleEditItem}
                          />
                        );
                      case 'action':
                      case 'submission':
                        return (
                          <ActionCard
                            status={card.status}
                            data={card.content}
                            timestamp={card.timestamp}
                            onRetry={retrySubmission}
                            onDownloadOrder={downloadOrder}
                            onStartNew={resetSession}
                          />
                        );
                      default:
                        return (
                          <ProcessingCard
                            title={card.title}
                            status={card.status}
                            content={card.content}
                            confidence={card.confidence}
                            timestamp={card.timestamp}
                          />
                        );
                    }
                  })();

                  return (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0, y: 50, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -20, scale: 0.95 }}
                      transition={{ 
                        duration: 0.5,
                        delay: index * 0.1,
                        type: "spring",
                        stiffness: 100,
                        damping: 20
                      }}
                      layout
                      layoutId={card.id}
                    >
                      {CardComponent}
                    </motion.div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Reset Button */}
          {hasActiveSession && (
            <motion.div 
              className="mt-8 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
            >
              <button
                onClick={resetSession}
                className="btn-secondary"
              >
                Process Another Document
              </button>
            </motion.div>
          )}
        </div>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;