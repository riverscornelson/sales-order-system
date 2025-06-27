import React, { useState, useCallback } from 'react';
import { Upload, FileText, Mail, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface UploadCardProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
}

export const UploadCard: React.FC<UploadCardProps> = ({ onFileUpload, isUploading }) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  }, [onFileUpload]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  }, [onFileUpload]);

  return (
    <motion.div 
      className="card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="card-header">
        <h3 className="card-title">Upload Document</h3>
        <div className="flex space-x-2">
          <div className="badge badge-blue">PDF</div>
          <div className="badge badge-blue">Email</div>
        </div>
      </div>

      <motion.div
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${isUploading ? 'opacity-50 pointer-events-none' : 'hover:border-blue-400 hover:bg-gray-50'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        whileHover={!isUploading ? { scale: 1.02 } : {}}
        whileTap={!isUploading ? { scale: 0.98 } : {}}
        animate={dragActive ? { 
          scale: 1.02,
          borderColor: "#3b82f6",
          backgroundColor: "#eff6ff"
        } : {}}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        <input
          type="file"
          accept=".pdf,.eml,.msg,.txt"
          onChange={handleChange}
          disabled={isUploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <AnimatePresence mode="wait">
          {isUploading ? (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="space-y-4"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="flex justify-center"
              >
                <Loader2 className="w-12 h-12 text-blue-500" />
              </motion.div>
              
              <div>
                <p className="text-lg font-medium text-gray-900">
                  Uploading Document...
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Please wait while we process your file
                </p>
              </div>
              
              <motion.div 
                className="w-full bg-gray-200 rounded-full h-2"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 2 }}
              >
                <motion.div 
                  className="bg-blue-500 h-2 rounded-full"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 2, ease: "easeInOut" }}
                />
              </motion.div>
            </motion.div>
          ) : (
            <motion.div
              key="upload"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="space-y-4"
            >
              <div className="flex justify-center space-x-4">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  transition={{ type: "spring", stiffness: 400, damping: 10 }}
                >
                  <Upload className={`w-12 h-12 transition-colors ${dragActive ? 'text-blue-500' : 'text-gray-400'}`} />
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.1, y: -5 }}
                  transition={{ type: "spring", stiffness: 400, damping: 10 }}
                >
                  <FileText className="w-12 h-12 text-blue-400" />
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.1, rotate: -5 }}
                  transition={{ type: "spring", stiffness: 400, damping: 10 }}
                >
                  <Mail className="w-12 h-12 text-green-400" />
                </motion.div>
              </div>
              
              <motion.div
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                <p className="text-lg font-medium text-gray-900">
                  {dragActive ? 'Drop it like it\'s hot!' : 'Drop your order document here'}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  or click to browse files
                </p>
              </motion.div>
              
              <motion.div 
                className="text-xs text-gray-400"
                initial={{ y: 10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                Supports PDF files and email formats (.eml, .msg)
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
};