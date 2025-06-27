import React from 'react';
import { motion } from 'framer-motion';
import { User, Package, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { ProcessingStatus, ConfidenceLevel } from '../types/api';

interface ExtractionData {
  customer?: {
    name?: string;
    company?: string;
    email?: string;
    phone?: string;
  };
  line_items_count?: number;
  line_items?: Array<{
    description: string;
    quantity?: number;
    part_number?: string;
  }>;
  confidence?: number;
}

interface ExtractionCardProps {
  status: ProcessingStatus;
  data: ExtractionData;
  timestamp: string;
}

export const ExtractionCard: React.FC<ExtractionCardProps> = ({
  status,
  data,
  timestamp
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case ProcessingStatus.ERROR:
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Clock className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <div className="badge badge-green">Extraction Complete</div>;
      case ProcessingStatus.ERROR:
        return <div className="badge badge-red">Extraction Failed</div>;
      case ProcessingStatus.PROCESSING:
        return <div className="badge badge-blue">Extracting Data...</div>;
      default:
        return <div className="badge badge-yellow">Pending</div>;
    }
  };

  const getConfidenceBadge = () => {
    const confidence = data.confidence || 0;
    if (confidence >= 0.8) {
      return <div className="badge badge-green">High Confidence</div>;
    } else if (confidence >= 0.6) {
      return <div className="badge badge-yellow">Medium Confidence</div>;
    } else if (confidence > 0) {
      return <div className="badge badge-red">Low Confidence</div>;
    }
    return null;
  };

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
          <h3 className="card-title">Order Data Extraction</h3>
        </div>
        <div className="flex space-x-2">
          {getStatusBadge()}
          {getConfidenceBadge()}
        </div>
      </div>

      <div className="space-y-6">
        {/* Customer Information */}
        {data.customer && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-50 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2 mb-3">
              <User className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-gray-900">Customer Information</h4>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              {data.customer.name && (
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{data.customer.name}</span>
                </div>
              )}
              {data.customer.company && (
                <div>
                  <span className="text-gray-600">Company:</span>
                  <span className="ml-2 font-medium">{data.customer.company}</span>
                </div>
              )}
              {data.customer.email && (
                <div>
                  <span className="text-gray-600">Email:</span>
                  <span className="ml-2 font-medium text-blue-600">{data.customer.email}</span>
                </div>
              )}
              {data.customer.phone && (
                <div>
                  <span className="text-gray-600">Phone:</span>
                  <span className="ml-2 font-medium">{data.customer.phone}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Line Items Summary */}
        {(data.line_items_count || data.line_items) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-50 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2 mb-3">
              <Package className="w-4 h-4 text-green-600" />
              <h4 className="font-medium text-gray-900">Line Items</h4>
              {data.line_items_count && (
                <span className="badge badge-blue">{data.line_items_count} items</span>
              )}
            </div>

            {data.line_items && data.line_items.length > 0 ? (
              <div className="space-y-3">
                {data.line_items.slice(0, 3).map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="bg-white rounded border border-gray-200 p-3"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs text-gray-500">Item {index + 1}</span>
                      {item.quantity && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          Qty: {item.quantity}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-900 mb-1">{item.description}</p>
                    
                    {item.part_number && (
                      <p className="text-xs text-gray-600">
                        Part #: <span className="font-mono">{item.part_number}</span>
                      </p>
                    )}
                  </motion.div>
                ))}
                
                {data.line_items.length > 3 && (
                  <div className="text-center py-2">
                    <span className="text-sm text-gray-500">
                      +{data.line_items.length - 3} more items
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-600">
                {data.line_items_count ? `${data.line_items_count} items found` : 'No items extracted'}
              </p>
            )}
          </motion.div>
        )}

        {/* Confidence Score */}
        {data.confidence && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-between text-sm"
          >
            <span className="text-gray-600">Extraction Confidence:</span>
            <div className="flex items-center space-x-2">
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full ${
                    data.confidence >= 0.8 ? 'bg-green-500' :
                    data.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${data.confidence * 100}%` }}
                  transition={{ delay: 0.5, duration: 0.8 }}
                />
              </div>
              <span className="font-medium">{Math.round(data.confidence * 100)}%</span>
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