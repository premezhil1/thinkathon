import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {   
  Alert,
  Snackbar 
} from '@mui/material';
 
import { AudioUploader } from '../components/AudioUploader';
import { ProcessingStatus } from '../components/ProcessingStatus';
import axios from 'axios';

interface ProcessingInfo {
  analysisId: string;
  status: string;
  progress: number;
  stage: string;
  message: string;
}

interface TopicSentimentData {
  topic: string;
  positive: number;
  neutral: number;
  negative: number;
  totalCount: number;
}

interface DashboardStats {
  topicSentiments: TopicSentimentData[];
  totalAnalyses: number;
  avgSentimentScore: number;
}

export const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [processingInfo, setProcessingInfo] = useState<ProcessingInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const processingRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();


  useEffect(() => {
    if (processingInfo && processingRef.current) {
      setTimeout(() => {
        scrollToProcessing();
      }, 600); // 200ms works well
    }
  }, [processingInfo]);

  const scrollToProcessing = () => {
    if (processingRef.current) {
      const headerOffset = 80; // adjust if your header is taller
      const elementPosition = processingRef.current.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - headerOffset;
  
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
    }
  };

  const handleUploadSuccess = (analysisId: string) => {

    setProcessingInfo({
      analysisId,
      status: 'processing',
      progress: 0,
      stage: 'upload',
      message: 'File uploaded successfully',
    });


    setSuccess('Audio file uploaded successfully! Processing started...');
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleProcessingComplete = (analysisId: string) => {
    setSuccess('Analysis completed successfully!');
    setTimeout(() => {
      navigate(`/results/${analysisId}`);
    }, 2000);
  };

  const handleProcessingError = (errorMessage: string) => {
    setError(errorMessage);
    setProcessingInfo(null);
  };

  return (
    <div className="page-container">
      <div className="mb-xl">
        <h1 className="page-title">
          {t('upload_header')}
        </h1>
      </div>

      <div className="grid-container grid-2-cols">
        <div>
          <div className="app-card">
            <div className="app-card-content">
              <h3 className="card-title">                
                {t('upload_title')}
              </h3>
              <p className="card-subtitle mb-lg">
              {t('upload_industryUpload')}
              </p>

              <AudioUploader
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </div>
          </div>
        </div>

        <div>
          <div className="app-card">
            <div className="app-card-content">
              <h3 className="card-title">
                {t('upload_features')}
              </h3>
              <div className="flex flex-col gap-md">
                <div className="app-card" style={{ backgroundColor: 'rgba(25, 118, 210, 0.05)', border: '1px solid rgba(25, 118, 210, 0.2)' }}>
                  <div className="p-md">
                    <h4 style={{ color: 'var(--primary-color)', marginTop: 'var(--spcing-xs)', marginBottom: 'var(--spacing-xs)' }}>
                      🎯 {t('upload_intentDetection')}
                    </h4>
                    <p style={{ color: '#666', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                      {t('upload_intentDescription')}
                    </p>
                  </div>
                </div>

                <div className="app-card" style={{ backgroundColor: 'rgba(220, 0, 78, 0.05)', border: '1px solid rgba(220, 0, 78, 0.2)' }}>
                  <div className="p-md">
                    <h4 style={{ color: 'var(--secondary-color)', marginTop: 'var(--spcing-xs)', marginBottom: 'var(--spacing-xs)' }}>
                      😊 {t('upload_sentimentAnalysis')}
                    </h4>
                    <p style={{ color: '#666', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                      {t('upload_sentimentDescription')}
                    </p>
                  </div>
                </div>

                <div className="app-card" style={{ backgroundColor: 'rgba(76, 175, 80, 0.05)', border: '1px solid rgba(76, 175, 80, 0.2)' }}>
                  <div className="p-md">
                    <h4 style={{ color: 'var(--success-color)', marginTop: 'var(--spcing-xs)', marginBottom: 'var(--spacing-xs)' }}>
                      📊 {t('upload_topicModeling')}
                    </h4>
                    <p style={{ color: '#666', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                      {t('upload_topicDescription')}
                    </p>
                  </div>
                </div>

                <div className="app-card" style={{ backgroundColor: 'rgba(255, 152, 0, 0.05)', border: '1px solid rgba(255, 152, 0, 0.2)' }}>
                  <div className="p-md">
                    <h4 style={{ color: 'var(--warning-color)', marginTop: 'var(--spcing-xs)', marginBottom: 'var(--spacing-xs)' }}>
                      📈 {t('upload_qualityScoring')}
                    </h4>
                    <p style={{ color: '#666', fontSize: 'var(--font-size-sm)', margin: 0 }}>
                      {t('upload_qualityDescription')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


      </div>

      {processingInfo && (
        <div ref={processingRef} className="grid-container grid-1-cols">
          <ProcessingStatus
            analysisId={processingInfo.analysisId}
            onComplete={handleProcessingComplete}
            onError={handleProcessingError}
          />
        </div>
      )}


      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>
    </div>
  );
};
