import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Send, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  ArrowRight,
  Download,
  RefreshCw
} from 'lucide-react';
import { ProcessingStatus } from '../types/api';

interface ActionData {
  order_id?: string;
  status?: 'submitted' | 'failed' | 'pending';
  message?: string;
  estimated_delivery?: string;
  draft_order_id?: string;
  total_amount?: number;
  error?: string;
  retry_count?: number;
  max_retries?: number;
}

interface ActionCardProps {
  status: ProcessingStatus;
  data: ActionData;
  timestamp: string;
  onRetry?: () => void;
  onDownloadOrder?: () => void;
  onStartNew?: () => void;
}

export const ActionCard: React.FC<ActionCardProps> = ({
  status,
  data,
  timestamp,
  onRetry,
  onDownloadOrder,
  onStartNew
}) => {
  const [isRetrying, setIsRetrying] = useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return data.status === 'submitted' ? 
          <CheckCircle className="w-5 h-5 text-green-600" /> :
          <XCircle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.ERROR:
        return <XCircle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Clock className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Send className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    if (status === ProcessingStatus.COMPLETED && data.status === 'submitted') {
      return <div className="badge badge-green">Order Submitted</div>;
    } else if (status === ProcessingStatus.ERROR || data.status === 'failed') {
      return <div className="badge badge-red">Submission Failed</div>;
    } else if (status === ProcessingStatus.PROCESSING) {
      return <div className="badge badge-blue">Submitting...</div>;
    }
    return <div className="badge badge-yellow">Pending Submission</div>;
  };

  const handleRetry = async () => {
    if (!onRetry) return;
    
    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  const isSuccess = status === ProcessingStatus.COMPLETED && data.status === 'submitted';
  const isFailed = status === ProcessingStatus.ERROR || data.status === 'failed';
  const canRetry = isFailed && onRetry && (data.retry_count || 0) < (data.max_retries || 3);

  return (
    <motion.div
      className="card"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      layout
    >
      <div className="card-header">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <h3 className="card-title">Order Submission</h3>
        </div>
        <div className="flex space-x-2">
          {getStatusBadge()}
        </div>
      </div>

      <div className="space-y-6">
        {/* Success State */}
        {isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-green-50 rounded-lg p-6 text-center"
          >
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
            
            <h4 className="text-lg font-semibold text-green-900 mb-2">
              Order Successfully Submitted!
            </h4>
            
            <p className="text-green-700 mb-4">
              {data.message || 'Your order has been submitted to the ERP system for processing.'}
            </p>

            {data.order_id && (
              <div className="bg-white rounded border border-green-200 p-4 mb-4">
                <div className="text-sm text-green-600 mb-1">Order ID</div>
                <div className="font-mono text-lg text-green-900">{data.order_id}</div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {data.total_amount && (
                <div className="bg-white rounded border border-green-200 p-3">
                  <div className="text-green-600">Total Amount</div>
                  <div className="font-semibold text-green-900">
                    ${data.total_amount.toLocaleString('en-US', { 
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2
                    })}
                  </div>
                </div>
              )}
              
              {data.estimated_delivery && (
                <div className="bg-white rounded border border-green-200 p-3">
                  <div className="text-green-600">Estimated Delivery</div>
                  <div className="font-semibold text-green-900">
                    {new Date(data.estimated_delivery).toLocaleDateString()}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Processing State */}
        {status === ProcessingStatus.PROCESSING && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-blue-50 rounded-lg p-6 text-center"
          >
            <Clock className="w-12 h-12 text-blue-600 mx-auto mb-4 animate-pulse" />
            
            <h4 className="text-lg font-semibold text-blue-900 mb-2">
              Submitting Order...
            </h4>
            
            <p className="text-blue-700 mb-4">
              Please wait while we submit your order to the ERP system.
            </p>

            <div className="flex items-center justify-center space-x-2 text-sm text-blue-600">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              <span className="ml-2">Processing</span>
            </div>
          </motion.div>
        )}

        {/* Error State */}
        {isFailed && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-red-50 rounded-lg p-6"
          >
            <div className="flex items-start space-x-4">
              <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
              
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-red-900 mb-2">
                  Order Submission Failed
                </h4>
                
                <p className="text-red-700 mb-4">
                  {data.error || data.message || 'An error occurred while submitting your order.'}
                </p>

                {data.retry_count !== undefined && data.max_retries !== undefined && (
                  <div className="text-sm text-red-600 mb-4">
                    Retry attempt {data.retry_count} of {data.max_retries}
                  </div>
                )}

                <div className="bg-white rounded border border-red-200 p-3 text-sm">
                  <div className="text-red-600 font-medium mb-1">What you can do:</div>
                  <ul className="text-red-700 space-y-1">
                    {canRetry && <li>• Try submitting the order again</li>}
                    <li>• Check your internet connection</li>
                    <li>• Contact support if the problem persists</li>
                    <li>• Download the order details for manual processing</li>
                  </ul>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-wrap justify-center gap-3"
        >
          {/* Retry Button */}
          {canRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="flex items-center space-x-2 btn-primary"
            >
              <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
              <span>{isRetrying ? 'Retrying...' : 'Retry Submission'}</span>
            </button>
          )}

          {/* Download Order */}
          {onDownloadOrder && (
            <button
              onClick={onDownloadOrder}
              className="flex items-center space-x-2 btn-secondary"
            >
              <Download className="w-4 h-4" />
              <span>Download Order</span>
            </button>
          )}

          {/* Start New Order */}
          {(isSuccess || isFailed) && onStartNew && (
            <button
              onClick={onStartNew}
              className="flex items-center space-x-2 btn-secondary"
            >
              <ArrowRight className="w-4 h-4" />
              <span>Process New Document</span>
            </button>
          )}
        </motion.div>

        {/* Additional Information */}
        {isSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-blue-50 rounded-lg p-4"
          >
            <h5 className="text-sm font-medium text-blue-900 mb-2">Next Steps</h5>
            <div className="text-sm text-blue-800 space-y-1">
              <div>• You will receive a confirmation email shortly</div>
              <div>• Order tracking information will be provided once available</div>
              <div>• Contact customer service for any questions about your order</div>
            </div>
          </motion.div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          {new Date(timestamp).toLocaleString()}
        </div>
      </div>
    </motion.div>
  );
};