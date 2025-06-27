import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileCheck, 
  Edit3, 
  Send, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign,
  Package,
  User,
  Clock,
  Eye,
  EyeOff
} from 'lucide-react';
import { ProcessingStatus } from '../types/api';

interface LineItem {
  line_number: number;
  original_description: string;
  matched_part_number?: string;
  matched_description?: string;
  quantity: number;
  unit_price?: number;
  line_total?: number;
  match_confidence?: number;
  requires_review?: boolean;
  has_issues?: boolean;
  alternatives?: Array<{
    part_number: string;
    description: string;
    unit_price: number;
    confidence_score: number;
  }>;
}

interface ReviewData {
  total_amount?: number;
  line_items_count?: number;
  matched_items?: number;
  items_requiring_review?: number;
  confidence?: string;
  line_items?: LineItem[];
  customer_info?: {
    name?: string;
    company?: string;
    email?: string;
    customer_id?: string;
    is_validated?: boolean;
  };
  recommendations?: Array<{
    type: string;
    priority: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    action: string;
  }>;
  attention_items?: Array<{
    type: string;
    severity: 'high' | 'medium' | 'low';
    title: string;
    description: string;
    action_required: string;
  }>;
}

interface ReviewCardProps {
  status: ProcessingStatus;
  data: ReviewData;
  timestamp: string;
  onSubmitOrder?: () => void;
  onEditItem?: (lineNumber: number) => void;
}

export const ReviewCard: React.FC<ReviewCardProps> = ({
  status,
  data,
  timestamp,
  onSubmitOrder,
  onEditItem
}) => {
  const [showAllItems, setShowAllItems] = useState(false);
  const [showAttentionItems, setShowAttentionItems] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const toggleItemExpansion = (lineNumber: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(lineNumber)) {
      newExpanded.delete(lineNumber);
    } else {
      newExpanded.add(lineNumber);
    }
    setExpandedItems(newExpanded);
  };

  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <FileCheck className="w-5 h-5 text-green-600" />;
      case ProcessingStatus.ERROR:
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Clock className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <FileCheck className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <div className="badge badge-green">Ready for Review</div>;
      case ProcessingStatus.ERROR:
        return <div className="badge badge-red">Review Preparation Failed</div>;
      case ProcessingStatus.PROCESSING:
        return <div className="badge badge-blue">Preparing Review...</div>;
      default:
        return <div className="badge badge-yellow">Pending</div>;
    }
  };

  const getConfidenceBadge = () => {
    if (!data.confidence) return null;
    
    const confidence = data.confidence.toLowerCase();
    const badgeClass = confidence === 'high' ? 'badge-green' : 
                      confidence === 'medium' ? 'badge-yellow' : 'badge-red';
    
    return <div className={`badge ${badgeClass}`}>{data.confidence} Confidence</div>;
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-blue-600" />;
    }
  };

  const displayItems = showAllItems ? data.line_items : data.line_items?.slice(0, 5);
  const hasIssues = data.attention_items && data.attention_items.length > 0;
  const canSubmit = status === ProcessingStatus.COMPLETED && !hasIssues;

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
          <h3 className="card-title">Order Review</h3>
        </div>
        <div className="flex space-x-2">
          {getStatusBadge()}
          {getConfidenceBadge()}
        </div>
      </div>

      <div className="space-y-6">
        {/* Order Summary */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              ${(data.total_amount || 0).toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </div>
            <div className="text-xs text-gray-600">Total Amount</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{data.line_items_count || 0}</div>
            <div className="text-xs text-gray-600">Line Items</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{data.matched_items || 0}</div>
            <div className="text-xs text-gray-600">Matched</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{data.items_requiring_review || 0}</div>
            <div className="text-xs text-gray-600">Need Review</div>
          </div>
        </motion.div>

        {/* Customer Information */}
        {data.customer_info && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-50 rounded-lg p-4"
          >
            <div className="flex items-center space-x-2 mb-3">
              <User className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-gray-900">Customer Information</h4>
              {data.customer_info.is_validated && (
                <CheckCircle className="w-4 h-4 text-green-600" />
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              {data.customer_info.name && (
                <div>
                  <span className="text-gray-600">Name:</span>
                  <span className="ml-2 font-medium">{data.customer_info.name}</span>
                </div>
              )}
              {data.customer_info.company && (
                <div>
                  <span className="text-gray-600">Company:</span>
                  <span className="ml-2 font-medium">{data.customer_info.company}</span>
                </div>
              )}
              {data.customer_info.email && (
                <div>
                  <span className="text-gray-600">Email:</span>
                  <span className="ml-2 font-medium text-blue-600">{data.customer_info.email}</span>
                </div>
              )}
              {data.customer_info.customer_id && (
                <div>
                  <span className="text-gray-600">Customer ID:</span>
                  <span className="ml-2 font-medium">{data.customer_info.customer_id}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Attention Items */}
        {data.attention_items && data.attention_items.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="border border-yellow-200 rounded-lg overflow-hidden"
          >
            <button
              onClick={() => setShowAttentionItems(!showAttentionItems)}
              className="w-full px-4 py-3 bg-yellow-50 hover:bg-yellow-100 transition-colors flex items-center justify-between"
            >
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Items Requiring Attention</span>
                <span className="badge badge-yellow">{data.attention_items.length}</span>
              </div>
              {showAttentionItems ? (
                <EyeOff className="w-4 h-4 text-yellow-600" />
              ) : (
                <Eye className="w-4 h-4 text-yellow-600" />
              )}
            </button>

            <AnimatePresence>
              {showAttentionItems && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-t border-yellow-200"
                >
                  <div className="p-4 space-y-3">
                    {data.attention_items.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start space-x-3 p-3 bg-white rounded border"
                      >
                        {getSeverityIcon(item.severity)}
                        
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900">
                            {item.title}
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            {item.description}
                          </div>
                          <div className="text-xs text-blue-600 mt-1 font-medium">
                            Action: {item.action_required}
                          </div>
                        </div>
                        
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.severity === 'high' ? 'bg-red-100 text-red-800' :
                          item.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {item.severity}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Line Items */}
        {data.line_items && data.line_items.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">Line Items</h4>
              {data.line_items.length > 5 && (
                <button
                  onClick={() => setShowAllItems(!showAllItems)}
                  className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-700"
                >
                  {showAllItems ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  <span>{showAllItems ? 'Show Less' : `Show All (${data.line_items.length})`}</span>
                </button>
              )}
            </div>

            <div className="space-y-2">
              {displayItems?.map((item) => (
                <motion.div
                  key={item.line_number}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`border rounded-lg overflow-hidden ${
                    item.has_issues ? 'border-red-200' : 
                    item.requires_review ? 'border-yellow-200' : 'border-gray-200'
                  }`}
                >
                  <div
                    className={`p-4 cursor-pointer transition-colors ${
                      item.has_issues ? 'bg-red-50 hover:bg-red-100' :
                      item.requires_review ? 'bg-yellow-50 hover:bg-yellow-100' :
                      'bg-white hover:bg-gray-50'
                    }`}
                    onClick={() => toggleItemExpansion(item.line_number)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-xs text-gray-500">Line {item.line_number}</span>
                          {item.matched_part_number && (
                            <span className="text-xs font-mono text-blue-600">
                              {item.matched_part_number}
                            </span>
                          )}
                          {item.requires_review && (
                            <span className="badge badge-yellow">Review</span>
                          )}
                          {item.has_issues && (
                            <span className="badge badge-red">Issues</span>
                          )}
                        </div>
                        
                        <p className="text-sm text-gray-900 mb-1">
                          {item.matched_description || item.original_description}
                        </p>
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-600">
                          <span>Qty: {item.quantity}</span>
                          {item.unit_price && (
                            <span>Price: ${item.unit_price.toFixed(2)}</span>
                          )}
                          {item.match_confidence && (
                            <span>Confidence: {Math.round(item.match_confidence * 100)}%</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        {item.line_total && (
                          <div className="text-sm font-medium text-gray-900">
                            ${item.line_total.toFixed(2)}
                          </div>
                        )}
                        
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onEditItem?.(item.line_number);
                          }}
                          className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>

                  <AnimatePresence>
                    {expandedItems.has(item.line_number) && item.alternatives && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-t border-gray-200 bg-gray-50"
                      >
                        <div className="p-4">
                          <h5 className="text-xs font-medium text-gray-700 mb-2">
                            Alternative Parts ({item.alternatives.length})
                          </h5>
                          <div className="space-y-2">
                            {item.alternatives.map((alt, altIndex) => (
                              <div key={altIndex} className="flex items-center justify-between text-xs bg-white p-2 rounded">
                                <div className="flex-1 min-w-0">
                                  <span className="font-mono text-blue-600">{alt.part_number}</span>
                                  <span className="ml-2 text-gray-600 truncate">{alt.description}</span>
                                </div>
                                <div className="flex items-center space-x-2 ml-2">
                                  <span>${alt.unit_price.toFixed(2)}</span>
                                  <span className="text-gray-500">
                                    {Math.round(alt.confidence_score * 100)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex justify-between items-center pt-4 border-t border-gray-200"
        >
          <div className="text-sm text-gray-600">
            {canSubmit ? (
              <span className="text-green-600">✅ Ready to submit order</span>
            ) : hasIssues ? (
              <span className="text-yellow-600">⚠️ Address attention items before submitting</span>
            ) : (
              <span>Review in progress...</span>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              className="btn-secondary"
              onClick={() => window.print()}
            >
              Print Review
            </button>
            
            <button
              className={`flex items-center space-x-2 ${
                canSubmit ? 'btn-primary' : 'btn-primary opacity-50 cursor-not-allowed'
              }`}
              onClick={onSubmitOrder}
              disabled={!canSubmit}
            >
              <Send className="w-4 h-4" />
              <span>Submit Order</span>
            </button>
          </div>
        </motion.div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          {new Date(timestamp).toLocaleString()}
        </div>
      </div>
    </motion.div>
  );
};