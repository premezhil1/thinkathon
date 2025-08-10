import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Grid,
  Paper,
  Divider,
} from '@mui/material';
import { CheckCircle, Error, Schedule, Group, Star, Psychology, AccessTime } from '@mui/icons-material';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

interface ProcessingStatusProps {
  analysisId: string;
  onComplete: (analysisId: string) => void;
  onError: (error: string) => void;
}

interface StatusUpdate {
  analysis_id: string;
  status: string;
  progress: number;
  stage: string;
  message: string;
  timestamp: string;
}

interface AnalysisResults {
  conversation_data: any;
  intent_results: any;
  sentiment_results: any;
  topic_results: any;
  quality_score: number;
  participants: string[];
  duration: number;
  industry: string;
}

const stages = [
  { key: 'upload', label: 'File Upload', description: 'Uploading audio file' },
  { key: 'transcription', label: 'Transcription', description: 'Converting speech to text' },
  { key: 'diarization', label: 'Speaker Identification', description: 'Identifying speakers' },
  { key: 'analysis', label: 'NLP Analysis', description: 'Analyzing intent and sentiment' },
  { key: 'saving', label: 'Saving', description: 'Saving analysis metrics' },
  { key: 'completed', label: 'Completed', description: 'Analysis finished successfully' },
];

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  analysisId,
  onComplete,
  onError,
}) => {
  const { t } = useTranslation();
  const [status, setStatus] = useState<StatusUpdate | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);

  const fetchAnalysisResults = async () => {
    try {
      const response = await axios.get(`/api/results/${analysisId}`);
      setAnalysisResults(response.data);
    } catch (error) {
      console.error('Error fetching analysis results:', error);
    }
  };

  useEffect(() => {
    let ws: WebSocket | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(`ws://localhost:8000/ws/${analysisId}`);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
        };
        
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setStatus(data);
          
          // Update active step based on stage
          const stageIndex = stages.findIndex(stage => stage.key === data.stage);
          if (stageIndex !== -1) {
            setActiveStep(stageIndex);
          }
          
          if (data.status === 'completed') {
            fetchAnalysisResults();
            onComplete(analysisId);
          } else if (data.status === 'error') {
            onError(data.message);
          }
        };
        
        ws.onerror = (error) => {
          console.log('WebSocket error, falling back to polling:', error);
          startPolling();
        };

        ws.onclose = () => {
          console.log('WebSocket closed, falling back to polling');
          startPolling();
        };
      } catch (error) {
        console.log('WebSocket connection failed, using polling:', error);
        startPolling();
      }
    };

    const startPolling = () => {
      if (pollInterval) return;
      
      pollInterval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/status/${analysisId}`);
          const data = response.data;
          setStatus(data);
          
          const stageIndex = stages.findIndex(stage => stage.key === data.stage);
          if (stageIndex !== -1) {
            setActiveStep(stageIndex);
          }
          
          if (data.status === 'completed') {
            fetchAnalysisResults();
            onComplete(analysisId);
            if (pollInterval) clearInterval(pollInterval);
          } else if (data.status === 'error') {
            onError(data.message);
            if (pollInterval) clearInterval(pollInterval);
          }
        } catch (error) {
          console.error('Error polling status:', error);
        }
      }, 2000);
    };

    console.log('Attempting WebSocket connection...');
    connectWebSocket();
    
    setTimeout(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.log('WebSocket not ready, starting polling');
        startPolling();
      }
    }, 1000);

    return () => {
      if (ws) {
        ws.close();
      }
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [analysisId, onComplete, onError]);

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getQualityColor = (score: number) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    return 'error';
  };

  const getQualityLabel = (score: number) => {
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Fair';
    return 'Poor';
  };

  if (!status) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6">{t('processing_status')}</Typography>
          <LinearProgress sx={{ mt: 2 }} />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {t('initializing')}
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'processing':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle />;
      case 'error':
        return <Error />;
      case 'processing':
        return <Schedule />;
      default:
        return <Schedule />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">{t('processing_status')}</Typography>
          <Chip
            icon={getStatusIcon(status.status)}
            label={t(`status_${status.status}`)}
            color={getStatusColor(status.status) as any}
            variant="outlined"
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {status.message}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {status.progress}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={status.progress} 
            color={getStatusColor(status.status) as any}
          />
        </Box>

        <Stepper activeStep={activeStep} orientation="vertical">
          {stages.map((stage, index) => (
            <Step key={stage.key}>
              <StepLabel
                optional={
                  index === stages.length - 1 ? (
                    <Typography variant="caption">{t('last_step')}</Typography>
                  ) : null
                }
              >
                {t(`stage_${stage.key}`)}
              </StepLabel>
              <StepContent>
                <Typography variant="body2" color="text.secondary">
                  {t(`stage_${stage.key}_description`)}
                </Typography>
              </StepContent>
            </Step>
          ))}
        </Stepper>

        {/* Show analysis results when completed */}
        {status.status === 'completed' && analysisResults && (
          <>
            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" gutterBottom>
              {t('analysis_results')}
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Group sx={{ fontSize: 24, color: 'primary.main', mb: 1 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    {t('participants')}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Array.isArray(analysisResults.participants) 
                      ? analysisResults.participants.join(', ') 
                      : analysisResults.participants || t('not_available')}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <AccessTime sx={{ fontSize: 24, color: 'secondary.main', mb: 1 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    {t('duration')}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {analysisResults.duration ? formatDuration(analysisResults.duration) : t('not_available')}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Star sx={{ 
                    fontSize: 24, 
                    color: getQualityColor(analysisResults.quality_score || 0), 
                    mb: 1 
                  }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    {t('quality_score')}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {analysisResults.quality_score?.toFixed(1) || t('not_available')} / 10
                  </Typography>
                  <Chip 
                    label={getQualityLabel(analysisResults.quality_score || 0)} 
                    size="small" 
                    color={getQualityColor(analysisResults.quality_score || 0) as any}
                    sx={{ mt: 0.5 }}
                  />
                </Paper>
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Psychology sx={{ fontSize: 24, color: 'info.main', mb: 1 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    {t('intent')}
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {analysisResults.intent_results?.predicted_intent || t('not_available')}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </>
        )}

        {status.status === 'error' && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {status.message}
          </Alert>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
          {t('analysis_id')}: {analysisId}
        </Typography>
      </CardContent>
    </Card>
  );
};
