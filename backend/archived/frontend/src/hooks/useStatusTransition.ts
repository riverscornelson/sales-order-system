import { useState, useEffect } from 'react';
import { ProcessingStatus } from '../types/api';

interface StatusTransition {
  currentStatus: ProcessingStatus;
  previousStatus: ProcessingStatus | null;
  isTransitioning: boolean;
}

export const useStatusTransition = (status: ProcessingStatus) => {
  const [statusTransition, setStatusTransition] = useState<StatusTransition>({
    currentStatus: status,
    previousStatus: null,
    isTransitioning: false
  });

  useEffect(() => {
    if (status !== statusTransition.currentStatus) {
      // Start transition
      setStatusTransition(prev => ({
        currentStatus: status,
        previousStatus: prev.currentStatus,
        isTransitioning: true
      }));

      // End transition after animation duration
      const timer = setTimeout(() => {
        setStatusTransition(prev => ({
          ...prev,
          isTransitioning: false
        }));
      }, 500); // Match animation duration

      return () => clearTimeout(timer);
    }
  }, [status, statusTransition.currentStatus]);

  return statusTransition;
};

export const getStatusColor = (status: ProcessingStatus) => {
  switch (status) {
    case ProcessingStatus.PENDING:
      return {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        icon: 'text-yellow-600'
      };
    case ProcessingStatus.PROCESSING:
      return {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-blue-800',
        icon: 'text-blue-600'
      };
    case ProcessingStatus.COMPLETED:
      return {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-green-800',
        icon: 'text-green-600'
      };
    case ProcessingStatus.ERROR:
      return {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        icon: 'text-red-600'
      };
    default:
      return {
        bg: 'bg-gray-50',
        border: 'border-gray-200',
        text: 'text-gray-800',
        icon: 'text-gray-600'
      };
  }
};

export const getStatusAnimation = (status: ProcessingStatus, isTransitioning: boolean) => {
  const baseAnimation = {
    initial: { scale: 0.9, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: { type: "spring", stiffness: 300, damping: 25 }
  };

  if (isTransitioning) {
    return {
      ...baseAnimation,
      animate: { 
        ...baseAnimation.animate,
        rotate: status === ProcessingStatus.PROCESSING ? [0, 360] : 0
      },
      transition: {
        ...baseAnimation.transition,
        rotate: status === ProcessingStatus.PROCESSING ? {
          duration: 2,
          repeat: Infinity,
          ease: "linear"
        } : {}
      }
    };
  }

  return baseAnimation;
};