import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, Clock, Zap, Loader2 } from 'lucide-react';
import { ProcessingStatus } from '../types/api';
import { useStatusTransition, getStatusColor, getStatusAnimation } from '../hooks/useStatusTransition';

interface StatusBadgeProps {
  status: ProcessingStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showText?: boolean;
  animated?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
  showText = true,
  animated = true
}) => {
  const statusTransition = useStatusTransition(status);
  const colors = getStatusColor(status);
  const animation = getStatusAnimation(status, statusTransition.isTransitioning);

  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className={`${getSizeClass().icon} ${colors.icon}`} />;
      case ProcessingStatus.ERROR:
        return <AlertCircle className={`${getSizeClass().icon} ${colors.icon}`} />;
      case ProcessingStatus.PROCESSING:
        return animated ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className={`${getSizeClass().icon} ${colors.icon}`} />
          </motion.div>
        ) : (
          <Zap className={`${getSizeClass().icon} ${colors.icon} animate-pulse`} />
        );
      default:
        return <Clock className={`${getSizeClass().icon} ${colors.icon}`} />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return 'Completed';
      case ProcessingStatus.ERROR:
        return 'Error';
      case ProcessingStatus.PROCESSING:
        return 'Processing';
      default:
        return 'Pending';
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return {
          container: 'px-2 py-1 text-xs',
          icon: 'w-3 h-3',
          text: 'text-xs'
        };
      case 'lg':
        return {
          container: 'px-4 py-2 text-base',
          icon: 'w-6 h-6',
          text: 'text-base'
        };
      default:
        return {
          container: 'px-3 py-1 text-sm',
          icon: 'w-4 h-4',
          text: 'text-sm'
        };
    }
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        className={`
          inline-flex items-center space-x-2 rounded-full font-medium
          ${getSizeClass().container}
          ${colors.bg} ${colors.border} ${colors.text}
          border
        `}
        {...(animated ? animation : {})}
        layout
      >
        {showIcon && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1, type: "spring", stiffness: 300 }}
          >
            {getStatusIcon()}
          </motion.div>
        )}
        
        {showText && (
          <motion.span
            className={getSizeClass().text}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 }}
          >
            {getStatusText()}
          </motion.span>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

// Status transition indicator for when status changes
export const StatusTransitionIndicator: React.FC<{ status: ProcessingStatus }> = ({ status }) => {
  const statusTransition = useStatusTransition(status);

  if (!statusTransition.isTransitioning || !statusTransition.previousStatus) {
    return null;
  }

  return (
    <motion.div
      className="absolute inset-0 pointer-events-none"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-blue-400 to-purple-400 rounded-lg opacity-20"
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.2, 0.4, 0.2]
        }}
        transition={{
          duration: 0.5,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute inset-0 border-2 border-blue-400 rounded-lg"
        animate={{
          scale: [1, 1.1, 1.2],
          opacity: [0.8, 0.4, 0]
        }}
        transition={{
          duration: 0.5,
          ease: "easeOut"
        }}
      />
    </motion.div>
  );
};