import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Alert,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  AudioFile,
  Person,
  Schedule,
  Psychology,
  TrendingUp,
  Group,
  Star,
  PlayArrow,
  Download,
  Refresh,
} from '@mui/icons-material';
import axios from 'axios';

interface AudioFile {
  filename: string;
  size: number;
  created_at: string;
  path: string;
}

interface AnalysisResult {
  analysis_id: string;
  conversation_data: any;
  intent_results: any;
  sentiment_results: any;
  topic_results: any;
  quality_score: number;
  participants: string[];
  duration: number;
  industry: string;
  processed_at: string;
  audio_file_path: string;
}

interface UserStatusData {
  user_id: string;
  total_analyses: number;
  audio_files: AudioFile[];
  recent_analyses: AnalysisResult[];
  status: string;
}

export const UserStatus: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const { t } = useTranslation();
  const [statusData, setStatusData] = useState<UserStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUserStatus = async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`/api/user/${userId}/status`);
      setStatusData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || t('failedToFetchUserStatus'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserStatus();
  }, [userId]);

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

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
    if (score >= 8) return t('excellent');
    if (score >= 6) return t('good');
    if (score >= 4) return t('fair');
    return t('poor');
  };

  if (loading) {
    return (
      <div className="page-container user-status-loading">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">
            {t('loadingUserStatus')}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container user-status-error-container">
        <Alert severity="error" action={
          <IconButton onClick={fetchUserStatus}>
            <Refresh />
          </IconButton>
        }>
          {error}
        </Alert>
      </div>
    );
  }

  if (!statusData) {
    return (
      <div className="page-container user-status-no-data-container">
        <Alert severity="info">
          {t('noUserDataFound')}
        </Alert>
      </div>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
          <Person fontSize="large" />
        </Avatar>
        <Box>
          <Typography variant="h4" component="h1">
            {statusData.user_id}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t('userStatus')} : <Chip label={statusData.status} color="primary" size="small" />
          </Typography>
        </Box>
        <Box sx={{ ml: 'auto' }}>
          <Tooltip title={t('refreshData')}>
            <IconButton onClick={fetchUserStatus}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={4}>
        {/* Overview Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Psychology sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {statusData.total_analyses}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('totalAnalyses')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AudioFile sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {statusData.audio_files.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('savedAudioFiles')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" component="div">
                {statusData.recent_analyses.length > 0 
                  ? statusData.recent_analyses[0].quality_score?.toFixed(1) || 'N/A'
                  : 'N/A'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('latestQualityScore')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Audio Files */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <h3 className="user-status-section-title">
                <AudioFile /> {t('savedAudioFiles')}
              </h3>
              {statusData.audio_files.length === 0 ? (
                <Alert severity="info">
                  {t('noAudioFilesUploaded')}
                </Alert>
              ) : (
                <List>
                  {statusData.audio_files.map((file, index) => (
                    <React.Fragment key={index}>
                      <ListItem className="user-status-list-item">
                        <ListItemIcon>
                          <AudioFile color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={file.filename}
                          secondary={
                            <div>
                              <p className="text-caption">
                                {t('size')} : {formatFileSize(file.size)}
                              </p>
                              <p className="text-caption">
                                {t('uploaded')} : {new Date(file.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          }
                        />
                        <div>
                          <Tooltip title={t('playAudio')}>
                            <IconButton size="small">
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={t('download')}>
                            <IconButton size="small">
                              <Download />
                            </IconButton>
                          </Tooltip>
                        </div>
                      </ListItem>
                      {index < statusData.audio_files.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Analyses */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Psychology /> {t('recentAnalyses')}
              </Typography>
              {statusData.recent_analyses.length === 0 ? (
                <Alert severity="info">
                  {t('noAnalysesCompleted')}
                </Alert>
              ) : (
                <List>
                  {statusData.recent_analyses.map((analysis, index) => (
                    <React.Fragment key={analysis.analysis_id}>
                      <ListItem sx={{ px: 0, flexDirection: 'column', alignItems: 'stretch' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1 }}>
                          <Typography variant="subtitle2">
                            {t('analysis')} {analysis.analysis_id.slice(0, 8)}...
                          </Typography>
                          <Chip 
                            label={analysis.industry} 
                            size="small" 
                            color="primary" 
                            variant="outlined" 
                          />
                        </Box>
                        
                        <Grid container spacing={2} sx={{ mb: 1 }}>
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, textAlign: 'center' }}>
                              <Group sx={{ fontSize: 20, color: 'text.secondary' }} />
                              <Typography variant="caption" display="block">
                                {t('participants')}
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {analysis.participants?.join(', ') || 'N/A'}
                              </Typography>
                            </Paper>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, textAlign: 'center' }}>
                              <Schedule sx={{ fontSize: 20, color: 'text.secondary' }} />
                              <Typography variant="caption" display="block">
                                {t('duration')}
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {analysis.duration ? formatDuration(analysis.duration) : 'N/A'}
                              </Typography>
                            </Paper>
                          </Grid>
                        </Grid>

                        <Grid container spacing={2} sx={{ mb: 1 }}>
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, textAlign: 'center' }}>
                              <Star sx={{ fontSize: 20, color: getQualityColor(analysis.quality_score) }} />
                              <Typography variant="caption" display="block">
                                {t('qualityScore')}
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {analysis.quality_score?.toFixed(1) || 'N/A'} / 10
                              </Typography>
                              <Chip 
                                label={getQualityLabel(analysis.quality_score || 0)} 
                                size="small" 
                                color={getQualityColor(analysis.quality_score || 0) as any}
                              />
                            </Paper>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Paper sx={{ p: 1, textAlign: 'center' }}>
                              <Psychology sx={{ fontSize: 20, color: 'text.secondary' }} />
                              <Typography variant="caption" display="block">
                                {t('intent')}
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {analysis.intent_results?.predicted_intent || 'N/A'}
                              </Typography>
                            </Paper>
                          </Grid>
                        </Grid>

                        <Typography variant="caption" color="text.secondary">
                          {t('processed')} : {new Date(analysis.processed_at).toLocaleString()}
                        </Typography>
                      </ListItem>
                      {index < statusData.recent_analyses.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};
