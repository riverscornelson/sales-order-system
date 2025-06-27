import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Package, 
  DollarSign, 
  User,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { ProcessingStatus } from '../types/api';

interface ERPValidationData {
  customer_valid?: boolean;
  customer_id?: string;
  inventory_available?: number;
  total_parts?: number;
  total_amount?: number;
  business_rules?: {
    overall_status: 'passed' | 'failed' | 'warning' | 'requires_approval';
    rules: Array<{
      rule: string;
      status: 'passed' | 'failed' | 'warning' | 'requires_approval';
      message: string;
    }>;
  };
  pricing_status?: 'available' | 'partial' | 'unavailable';
}

interface ERPValidationCardProps {
  status: ProcessingStatus;
  data: ERPValidationData;
  timestamp: string;
}

export const ERPValidationCard: React.FC<ERPValidationCardProps> = ({
  status,
  data,
  timestamp
}) => {
  const [showBusinessRules, setShowBusinessRules] = useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case ProcessingStatus.ERROR:
        return <XCircle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Shield className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Shield className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <div className="badge badge-green">Validation Complete</div>;
      case ProcessingStatus.ERROR:
        return <div className="badge badge-red">Validation Failed</div>;
      case ProcessingStatus.PROCESSING:
        return <div className="badge badge-blue">Validating...</div>;
      default:
        return <div className="badge badge-yellow">Pending</div>;
    }
  };

  const getOverallStatusBadge = () => {
    if (!data.business_rules) return null;

    const statusColors = {
      passed: 'badge-green',
      warning: 'badge-yellow',
      failed: 'badge-red',
      requires_approval: 'badge-blue'
    };

    const statusLabels = {
      passed: 'All Checks Passed',
      warning: 'Warning',
      failed: 'Validation Failed',
      requires_approval: 'Requires Approval'
    };

    const colorClass = statusColors[data.business_rules.overall_status];
    const label = statusLabels[data.business_rules.overall_status];

    return <div className={`badge ${colorClass}`}>{label}</div>;
  };

  const getRuleStatusIcon = (ruleStatus: string) => {
    switch (ruleStatus) {
      case 'passed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'requires_approval':
        return <AlertTriangle className="w-4 h-4 text-blue-600" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-400" />;
    }
  };

  const inventoryPercentage = data.total_parts ? 
    (data.inventory_available || 0) / data.total_parts * 100 : 0;

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
          <h3 className="card-title">ERP Validation</h3>
        </div>
        <div className="flex space-x-2">
          {getStatusBadge()}
          {getOverallStatusBadge()}
        </div>
      </div>

      <div className="space-y-4">
        {/* Validation Summary */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {/* Customer Validation */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <User className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-900">Customer</span>
            </div>
            
            <div className="flex items-center space-x-2">
              {data.customer_valid ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              <span className="text-sm text-gray-700">
                {data.customer_valid ? 'Validated' : 'Not Found'}
              </span>
            </div>
            
            {data.customer_id && (
              <div className="mt-1 text-xs text-gray-600">
                ID: {data.customer_id}
              </div>
            )}
          </div>

          {/* Inventory Status */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Package className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-900">Inventory</span>
            </div>
            
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-lg font-bold text-gray-900">
                {data.inventory_available || 0}/{data.total_parts || 0}
              </span>
              <span className="text-sm text-gray-600">available</span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className={`h-2 rounded-full ${
                  inventoryPercentage === 100 ? 'bg-green-500' :
                  inventoryPercentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${inventoryPercentage}%` }}
                transition={{ delay: 0.3, duration: 0.8 }}
              />
            </div>
            
            <div className="mt-1 text-xs text-gray-600">
              {inventoryPercentage.toFixed(0)}% available
            </div>
          </div>

          {/* Order Total */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-900">Order Total</span>
            </div>
            
            <div className="text-lg font-bold text-gray-900">
              ${(data.total_amount || 0).toLocaleString('en-US', { 
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              })}
            </div>
            
            <div className="flex items-center mt-1">
              <div className={`w-2 h-2 rounded-full mr-2 ${
                data.pricing_status === 'available' ? 'bg-green-500' :
                data.pricing_status === 'partial' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-xs text-gray-600 capitalize">
                Pricing {data.pricing_status || 'unknown'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Business Rules */}
        {data.business_rules && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            <button
              onClick={() => setShowBusinessRules(!showBusinessRules)}
              className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
            >
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-900">Business Rules</span>
                <span className="text-xs text-gray-600">
                  ({data.business_rules.rules.length} checks)
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-600 capitalize">
                  {data.business_rules.overall_status.replace('_', ' ')}
                </span>
                {showBusinessRules ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </div>
            </button>

            <AnimatePresence>
              {showBusinessRules && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-t border-gray-200"
                >
                  <div className="p-4 space-y-3">
                    {data.business_rules.rules.map((rule, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start space-x-3"
                      >
                        {getRuleStatusIcon(rule.status)}
                        
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 capitalize">
                            {rule.rule.replace(/_/g, ' ')}
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            {rule.message}
                          </div>
                        </div>
                        
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          rule.status === 'passed' ? 'bg-green-100 text-green-800' :
                          rule.status === 'failed' ? 'bg-red-100 text-red-800' :
                          rule.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {rule.status === 'requires_approval' ? 'Approval' : rule.status}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Validation Summary */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-blue-50 rounded-lg p-4"
        >
          <h4 className="text-sm font-medium text-blue-900 mb-2">Validation Summary</h4>
          <div className="text-sm text-blue-800">
            {data.business_rules?.overall_status === 'passed' && (
              <span>✅ Order validation successful. Ready for processing.</span>
            )}
            {data.business_rules?.overall_status === 'warning' && (
              <span>⚠️ Order validation completed with warnings. Review recommended.</span>
            )}
            {data.business_rules?.overall_status === 'failed' && (
              <span>❌ Order validation failed. Address issues before proceeding.</span>
            )}
            {data.business_rules?.overall_status === 'requires_approval' && (
              <span>📋 Order requires manual approval before processing.</span>
            )}
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