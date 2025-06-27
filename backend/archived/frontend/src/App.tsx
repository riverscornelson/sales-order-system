import { useState, useCallback } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useJobPolling, type JobStatus } from './hooks/useJobPolling';
import { apiService } from './services/api';

// Simple processing steps for user feedback
const PROCESSING_STEPS = [
  { id: 'upload', title: '📤 Upload Document', description: 'Uploading your file...' },
  { id: 'parse', title: '📝 Parse Document', description: 'Extracting text and structure...' },
  { id: 'extract', title: '🔍 Extract Items', description: 'Finding order line items...' },
  { id: 'match', title: '🎯 Match Parts', description: 'Matching with parts catalog...' },
  { id: 'validate', title: '✅ Validate Order', description: 'Checking for errors...' },
  { id: 'complete', title: '🎉 Complete', description: 'Order processing finished!' }
];

interface ProcessingState {
  jobId: string | null;
  fileName: string | null;
  fileSize: string | null;
  currentStep: string;
  results: any | null;
  error: string | null;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState<ProcessingState>({
    jobId: null,
    fileName: null,
    fileSize: null,
    currentStep: 'upload',
    results: null,
    error: null
  });

  // Poll job status when we have a jobId
  const { status: jobStatus, isPolling, error: pollingError } = useJobPolling(
    processing.jobId,
    {
      interval: 2000,
      onStatusChange: (status: JobStatus) => {
        setProcessing(prev => ({
          ...prev,
          currentStep: status.step || prev.currentStep,
          error: status.error || null
        }));
      },
      onComplete: (results: any) => {
        setProcessing(prev => ({
          ...prev,
          currentStep: 'complete',
          results: results
        }));
      },
      onError: (error: string) => {
        setProcessing(prev => ({
          ...prev,
          error: error
        }));
      }
    }
  );

  // Handle file selection and upload
  const handleFileSelect = useCallback(async (selectedFile: File) => {
    setFile(selectedFile);
    setUploading(true);
    setProcessing({
      jobId: null,
      fileName: selectedFile.name,
      fileSize: `${(selectedFile.size / 1024).toFixed(1)} KB`,
      currentStep: 'upload',
      results: null,
      error: null
    });

    try {
      const result = await apiService.uploadFile(selectedFile);
      
      setProcessing(prev => ({
        ...prev,
        jobId: result.session_id, // Use session_id as jobId
        currentStep: 'parse'
      }));
      
      setUploading(false);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploading(false);
      setProcessing(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Upload failed'
      }));
    }
  }, []);

  // Reset to start over
  const handleReset = useCallback(() => {
    setFile(null);
    setUploading(false);
    setProcessing({
      jobId: null,
      fileName: null,
      fileSize: null,
      currentStep: 'upload',
      results: null,
      error: null
    });
  }, []);

  // Get current step info
  const getCurrentStepInfo = () => {
    return PROCESSING_STEPS.find(step => step.id === processing.currentStep) || PROCESSING_STEPS[0];
  };

  // Calculate progress percentage
  const getProgress = () => {
    const currentIndex = PROCESSING_STEPS.findIndex(step => step.id === processing.currentStep);
    return currentIndex >= 0 ? ((currentIndex + 1) / PROCESSING_STEPS.length) * 100 : 0;
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              📋 Sales Order Entry System
            </h1>
            <p className="text-gray-600">
              Upload your order documents and let our AI process them for you
            </p>
          </div>

          {/* Main Content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            
            {/* File Upload Section */}
            {!file && (
              <div className="text-center">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-gray-400 transition-colors">
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept=".pdf,.txt,.eml,.msg"
                    onChange={(e) => {
                      const selectedFile = e.target.files?.[0];
                      if (selectedFile) handleFileSelect(selectedFile);
                    }}
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center"
                  >
                    <div className="text-4xl mb-4">📎</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Upload Your Order Document
                    </h3>
                    <p className="text-gray-500 mb-4">
                      Drag and drop or click to select PDF, email, or text files
                    </p>
                    <div className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors">
                      Choose File
                    </div>
                  </label>
                </div>
              </div>
            )}

            {/* Processing Section */}
            {file && (
              <div>
                {/* File Info */}
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{processing.fileName}</h3>
                      <p className="text-sm text-gray-500">{processing.fileSize}</p>
                    </div>
                    <button
                      onClick={handleReset}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                      title="Start Over"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-6">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Progress</span>
                    <span>{Math.round(getProgress())}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${getProgress()}%` }}
                    />
                  </div>
                </div>

                {/* Current Step */}
                <div className="mb-6 p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 mr-3">
                      {uploading || isPolling ? (
                        <div className="animate-spin text-2xl">⏳</div>
                      ) : processing.error ? (
                        <div className="text-2xl">❌</div>
                      ) : processing.currentStep === 'complete' ? (
                        <div className="text-2xl">✅</div>
                      ) : (
                        <div className="text-2xl">🔄</div>
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">
                        {getCurrentStepInfo().title}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {processing.error || getCurrentStepInfo().description}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Processing Steps List */}
                <div className="space-y-2 mb-6">
                  {PROCESSING_STEPS.map((step, index) => {
                    const currentIndex = PROCESSING_STEPS.findIndex(s => s.id === processing.currentStep);
                    const isCompleted = index < currentIndex || (processing.currentStep === 'complete' && index <= PROCESSING_STEPS.length - 1);
                    const isCurrent = step.id === processing.currentStep;
                    // const isPending = index > currentIndex;

                    return (
                      <div
                        key={step.id}
                        className={`flex items-center p-2 rounded ${
                          isCurrent ? 'bg-blue-50 border border-blue-200' :
                          isCompleted ? 'bg-green-50' : 'bg-gray-50'
                        }`}
                      >
                        <div className="mr-3">
                          {isCompleted ? '✅' : isCurrent ? '🔄' : '⏳'}
                        </div>
                        <span className={`text-sm ${
                          isCurrent ? 'font-medium text-blue-900' :
                          isCompleted ? 'text-green-800' : 'text-gray-500'
                        }`}>
                          {step.title}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Error Display */}
                {(processing.error || pollingError) && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center">
                      <div className="text-red-600 mr-2">❌</div>
                      <div>
                        <h3 className="font-medium text-red-800">Processing Error</h3>
                        <p className="text-sm text-red-600">
                          {processing.error || pollingError}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Results Display */}
                {processing.results && (
                  <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h3 className="font-medium text-green-800 mb-2">🎉 Processing Complete!</h3>
                    <div className="text-sm text-green-700">
                      <pre className="whitespace-pre-wrap bg-white p-3 rounded border">
                        {JSON.stringify(processing.results, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex justify-center space-x-4">
                  <button
                    onClick={handleReset}
                    className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                  >
                    🆕 Process Another Order
                  </button>
                  
                  {processing.results && (
                    <button
                      onClick={() => {
                        const dataStr = JSON.stringify(processing.results, null, 2);
                        const dataBlob = new Blob([dataStr], { type: 'application/json' });
                        const url = URL.createObjectURL(dataBlob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = `order-results-${Date.now()}.json`;
                        link.click();
                        URL.revokeObjectURL(url);
                      }}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      💾 Download Results
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Debug Info (only in development) */}
          {import.meta.env.DEV && (
            <div className="mt-8 p-4 bg-gray-100 rounded-lg text-xs text-gray-600">
              <details>
                <summary className="cursor-pointer font-medium">Debug Info</summary>
                <pre className="mt-2 whitespace-pre-wrap">
                  {JSON.stringify({ 
                    processing, 
                    jobStatus, 
                    isPolling, 
                    pollingError 
                  }, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;