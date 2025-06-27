import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, Clock, Zap, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import { ProcessingStatus, ConfidenceLevel } from '../types/api';
import { StatusBadge, StatusTransitionIndicator } from './StatusBadge';

interface ProcessingCardProps {
  title: string;
  status: ProcessingStatus;
  content: Record<string, any>;
  confidence?: ConfidenceLevel;
  timestamp: string;
}

export const ProcessingCard: React.FC<ProcessingCardProps> = ({
  title,
  status,
  content,
  confidence,
  timestamp
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case ProcessingStatus.ERROR:
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Zap className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <div className="badge badge-green">Completed</div>;
      case ProcessingStatus.ERROR:
        return <div className="badge badge-red">Error</div>;
      case ProcessingStatus.PROCESSING:
        return <div className="badge badge-blue">Processing</div>;
      default:
        return <div className="badge badge-yellow">Pending</div>;
    }
  };

  const getConfidenceBadge = () => {
    if (!confidence) return null;
    
    const badgeClass = {
      [ConfidenceLevel.HIGH]: 'badge-green',
      [ConfidenceLevel.MEDIUM]: 'badge-yellow',
      [ConfidenceLevel.LOW]: 'badge-red',
    }[confidence];

    return <div className={`badge ${badgeClass}`}>
      {confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence
    </div>;
  };

  // Separate essential and detailed content
  const contentEntries = Object.entries(content);
  const essentialEntries = contentEntries.slice(0, 3);
  const detailedEntries = contentEntries.slice(3);
  const hasMoreContent = detailedEntries.length > 0;

  return (
    <motion.div
      className="card group hover:shadow-lg relative"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4 }}
      layout
      whileHover={{ y: -2 }}
    >
      <StatusTransitionIndicator status={status} />
      <motion.div 
        className="card-header cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ backgroundColor: "rgba(0,0,0,0.02)" }}
        whileTap={{ scale: 0.98 }}
      >
        <div className="flex items-center space-x-3">
          <motion.div
            animate={status === ProcessingStatus.PROCESSING ? {
              rotate: [0, 360],
              transition: { duration: 2, repeat: Infinity, ease: "linear" }
            } : {}}
          >
            {getStatusIcon()}
          </motion.div>
          <h3 className="card-title">{title}</h3>
          
          {hasMoreContent && (
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </motion.div>
          )}
        </div>
        <div className="flex space-x-2">
          <StatusBadge status={status} size="md" animated={true} />
          {confidence && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
            >
              {getConfidenceBadge()}
            </motion.div>
          )}
        </div>
      </motion.div>

      <div className="space-y-4">
        {/* Essential Content - Always Visible */}
        {essentialEntries.map(([key, value], index) => (
          <motion.div 
            key={key} 
            className="border-l-4 border-gray-200 pl-4 hover:border-blue-300 transition-colors"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <div className="text-sm text-gray-600 uppercase tracking-wide">
              {key.replace(/_/g, ' ')}
            </div>
            <div className="mt-1 text-gray-900">
              {typeof value === 'object' ? (
                <motion.pre 
                  className="text-xs bg-gray-100 p-2 rounded overflow-x-auto"
                  whileHover={{ backgroundColor: "rgb(243 244 246)" }}
                >
                  {JSON.stringify(value, null, 2)}
                </motion.pre>
              ) : (
                <span>{String(value)}</span>
              )}
            </div>
          </motion.div>
        ))}

        {/* Detailed Content - Progressive Disclosure */}
        <AnimatePresence>
          {isExpanded && detailedEntries.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <motion.div className="space-y-4 pt-4 border-t border-gray-100">
                {detailedEntries.map(([key, value], index) => (
                  <motion.div 
                    key={key} 
                    className="border-l-4 border-blue-200 pl-4 hover:border-blue-400 transition-colors"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="text-sm text-blue-600 uppercase tracking-wide">
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div className="mt-1 text-gray-900">
                      {typeof value === 'object' ? (
                        <motion.pre 
                          className="text-xs bg-blue-50 p-2 rounded overflow-x-auto"
                          whileHover={{ backgroundColor: "rgb(239 246 255)" }}
                        >
                          {JSON.stringify(value, null, 2)}
                        </motion.pre>
                      ) : (
                        <span>{String(value)}</span>
                      )}
                    </div>
                  </motion.div>
                ))}

                {/* Raw Data Toggle */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="flex items-center justify-center pt-2"
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowRawData(!showRawData);
                    }}
                    className="flex items-center space-x-2 text-xs text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {showRawData ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    <span>{showRawData ? 'Hide Raw Data' : 'Show Raw Data'}</span>
                  </button>
                </motion.div>

                <AnimatePresence>
                  {showRawData && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded overflow-x-auto">
                        {JSON.stringify(content, null, 2)}
                      </pre>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <motion.div 
        className="mt-4 pt-4 border-t border-gray-200"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="text-xs text-gray-500">
          {new Date(timestamp).toLocaleString()}
        </div>
      </motion.div>
    </motion.div>
  );
};