import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, CheckCircle, AlertTriangle, ArrowRight, Zap, Eye, EyeOff } from 'lucide-react';
import { ProcessingStatus } from '../types/api';

interface PartMatch {
  part_number: string;
  description: string;
  material?: string;
  unit_price?: number;
  availability?: number;
  scores: {
    combined_score: number;
    vector_similarity?: number;
    text_similarity?: number;
  };
  match_explanation?: string;
}

interface MatchingData {
  total_parts?: number;
  matched_parts?: number;
  match_rate?: string;
  top_matches?: Array<[string, PartMatch[]]>;
  confidence?: number;
}

interface MatchingCardProps {
  status: ProcessingStatus;
  data: MatchingData;
  timestamp: string;
}

export const MatchingCard: React.FC<MatchingCardProps> = ({
  status,
  data,
  timestamp
}) => {
  const [expandedMatches, setExpandedMatches] = useState<Set<string>>(new Set());
  const [showAllMatches, setShowAllMatches] = useState(false);

  const toggleMatchExpansion = (itemKey: string) => {
    const newExpanded = new Set(expandedMatches);
    if (newExpanded.has(itemKey)) {
      newExpanded.delete(itemKey);
    } else {
      newExpanded.add(itemKey);
    }
    setExpandedMatches(newExpanded);
  };

  const getStatusIcon = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case ProcessingStatus.ERROR:
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case ProcessingStatus.PROCESSING:
        return <Zap className="w-5 h-5 text-blue-600 animate-pulse" />;
      default:
        return <Search className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case ProcessingStatus.COMPLETED:
        return <div className="badge badge-green">Matching Complete</div>;
      case ProcessingStatus.ERROR:
        return <div className="badge badge-red">Matching Failed</div>;
      case ProcessingStatus.PROCESSING:
        return <div className="badge badge-blue">Finding Matches...</div>;
      default:
        return <div className="badge badge-yellow">Pending</div>;
    }
  };

  const getMatchRateBadge = () => {
    if (!data.match_rate) return null;
    
    const rate = parseFloat(data.match_rate.replace('%', ''));
    let className = 'badge ';
    
    if (rate >= 80) {
      className += 'badge-green';
    } else if (rate >= 60) {
      className += 'badge-yellow';
    } else {
      className += 'badge-red';
    }

    return <div className={className}>{data.match_rate} matched</div>;
  };

  const getConfidenceScore = (score: number) => {
    if (score >= 0.8) return { color: 'text-green-600', bg: 'bg-green-100', label: 'High' };
    if (score >= 0.6) return { color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Medium' };
    return { color: 'text-red-600', bg: 'bg-red-100', label: 'Low' };
  };

  const displayMatches = showAllMatches ? data.top_matches : data.top_matches?.slice(0, 3);

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
          <h3 className="card-title">Parts Matching</h3>
        </div>
        <div className="flex space-x-2">
          {getStatusBadge()}
          {getMatchRateBadge()}
        </div>
      </div>

      <div className="space-y-4">
        {/* Matching Statistics */}
        {(data.total_parts || data.matched_parts) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-50 rounded-lg p-4"
          >
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-gray-900">{data.total_parts || 0}</div>
                <div className="text-xs text-gray-600">Total Parts</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{data.matched_parts || 0}</div>
                <div className="text-xs text-gray-600">Matched</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">{data.match_rate || '0%'}</div>
                <div className="text-xs text-gray-600">Success Rate</div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Part Matches */}
        {data.top_matches && data.top_matches.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">Part Matches</h4>
              {data.top_matches.length > 3 && (
                <button
                  onClick={() => setShowAllMatches(!showAllMatches)}
                  className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-700"
                >
                  {showAllMatches ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  <span>{showAllMatches ? 'Show Less' : `Show All (${data.top_matches.length})`}</span>
                </button>
              )}
            </div>

            <AnimatePresence>
              {displayMatches?.map(([itemKey, matches], index) => {
                const bestMatch = matches[0];
                const isExpanded = expandedMatches.has(itemKey);
                const confidence = getConfidenceScore(bestMatch?.scores?.combined_score || 0);

                return (
                  <motion.div
                    key={itemKey}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ delay: index * 0.1 }}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <div
                      className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                      onClick={() => toggleMatchExpansion(itemKey)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-xs text-gray-500">Item {itemKey.split('_')[1]}</span>
                            <ArrowRight className="w-3 h-3 text-gray-400" />
                            <span className="text-xs font-mono text-blue-600">
                              {bestMatch?.part_number}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-900 truncate">
                            {bestMatch?.description}
                          </p>
                          
                          {bestMatch?.material && (
                            <p className="text-xs text-gray-600 mt-1">
                              {bestMatch.material}
                            </p>
                          )}
                        </div>

                        <div className="flex items-center space-x-2 ml-4">
                          <div className={`px-2 py-1 rounded-full text-xs font-medium ${confidence.bg} ${confidence.color}`}>
                            {Math.round((bestMatch?.scores?.combined_score || 0) * 100)}%
                          </div>
                          
                          {bestMatch?.unit_price && (
                            <div className="text-xs text-gray-600">
                              ${bestMatch.unit_price.toFixed(2)}
                            </div>
                          )}
                        </div>
                      </div>

                      {bestMatch?.match_explanation && (
                        <div className="mt-2 text-xs text-gray-500">
                          {bestMatch.match_explanation}
                        </div>
                      )}
                    </div>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-gray-200 bg-gray-50"
                        >
                          <div className="p-4 space-y-3">
                            {/* Best Match Details */}
                            <div>
                              <h5 className="text-xs font-medium text-gray-700 mb-2">Best Match Details</h5>
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div>
                                  <span className="text-gray-500">Vector Similarity:</span>
                                  <span className="ml-1 font-medium">
                                    {Math.round((bestMatch?.scores?.vector_similarity || 0) * 100)}%
                                  </span>
                                </div>
                                <div>
                                  <span className="text-gray-500">Text Similarity:</span>
                                  <span className="ml-1 font-medium">
                                    {Math.round((bestMatch?.scores?.text_similarity || 0) * 100)}%
                                  </span>
                                </div>
                                {bestMatch?.availability && (
                                  <div>
                                    <span className="text-gray-500">Available:</span>
                                    <span className="ml-1 font-medium">{bestMatch.availability}</span>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Alternative Matches */}
                            {matches.length > 1 && (
                              <div>
                                <h5 className="text-xs font-medium text-gray-700 mb-2">
                                  Alternative Matches ({matches.length - 1})
                                </h5>
                                <div className="space-y-2">
                                  {matches.slice(1, 4).map((match, altIndex) => {
                                    const altConfidence = getConfidenceScore(match.scores.combined_score);
                                    return (
                                      <div key={altIndex} className="flex items-center justify-between text-xs">
                                        <div className="flex-1 min-w-0">
                                          <span className="font-mono text-blue-600">{match.part_number}</span>
                                          <span className="ml-2 text-gray-600 truncate">{match.description}</span>
                                        </div>
                                        <div className={`px-1.5 py-0.5 rounded text-xs ${altConfidence.bg} ${altConfidence.color}`}>
                                          {Math.round(match.scores.combined_score * 100)}%
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Overall Confidence */}
        {data.confidence && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex items-center justify-between text-sm"
          >
            <span className="text-gray-600">Overall Matching Confidence:</span>
            <div className="flex items-center space-x-2">
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full ${
                    data.confidence >= 0.8 ? 'bg-green-500' :
                    data.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${data.confidence * 100}%` }}
                  transition={{ delay: 0.6, duration: 0.8 }}
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