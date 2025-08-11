import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Avatar,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Paper,
  Divider,
  Button,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack,
  AudioFile,
  PlayArrow,
  TrendingUp,
  Phone,
  Schedule,
  Star,
  Psychology,
  Download,
  Business,
  Group,
  Refresh,
  DateRange,
  Assessment,
  SentimentSatisfied,
  SentimentNeutral,
  SentimentDissatisfied,
  CheckCircle,
  Warning,
  Error,
  AdminPanelSettings,
  SupervisorAccount,
  PersonOutline,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import axios from 'axios';

interface User {
  user_id: string;
  username: string;
  email: string;
  full_name: string;
  department: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

 

 const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

interface BasicMetrics {
  total_calls: number;
  avg_quality_score: number;
  avg_call_duration: number;
  total_call_duration: number;
  first_call_date: string;
  last_call_date: string;
}


interface UserStatusData {
  user_id: string;
  total_analyses: number;
  audio_files: AudioFile[];
  recent_analyses: Analysis[];
  status: string;
}

interface Analysis {
  analysis: AnalysisResult;
  sentiment: string;
  analysis_id: string;
  conversation_data: any;
  intents: [{intent: string}];
  sentiment_results: any;
  topic_results: any;
  quality_score: number;
  participants: string[];
  duration: number;
  industry: string;
  processed_at: string;
  audio_file_path: string;
}

interface AnalysisResult {
  analysis_id: string;
  conversation_data: any;
  sentiment: string;
  intents: [{intent: string}];
  sentiment_results: any;
  topic_results: any;
  quality_score: number;
  participants: string[];
  duration: number;
  industry: string;
  processed_at: string;
  audio_file_path: string;
}

interface AudioFile {
  filename: string;
  size: number;
  created_at: string;
  path: string;
}


interface PerformanceData {
  user_id: string;
  user_info: User;
  basic_metrics: BasicMetrics;
  sentiment_distribution: Record<string, { count: number; avg_score: number }>;
  industry_distribution: Record<string, { count: number; avg_quality: number }>;
  quality_distribution: Record<string, number>;
  performance_trend: Array<{ call_date: string; daily_calls: number; daily_avg_quality: number }>;
  top_intents: Array<{ top_intent: string; count: number }>;
  date_range: { from: string | null; to: string | null };
}


const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'success';
      case 'negative':
        return 'error';
      case 'neutral':
        return 'default';
      default:
        return 'default';
    }
  };

export const UserDashboard: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<UserStatusData | null>(null);


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
  const fetchPerformanceData = async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`/api/users/${userId}/performance`);
      setPerformanceData(response.data.performance);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch user performance data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPerformanceData();
    fetchUserStatus();
  }, [userId]);

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <AdminPanelSettings />;
      case 'manager':
        return <SupervisorAccount />;
      default:
        return <PersonOutline />;
    }
  };

  const getQualityLabel = (score: number) => {
    if (score >= 8) return t('excellent');
    if (score >= 6) return t('good');
    if (score >= 4) return t('fair');
    return t('poor');
  };

  const getRoleColor = (role: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'manager':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getAvatarColor = (role: string) => {
    switch (role) {
      case 'admin':
        return '#f44336';
      case 'manager':
        return '#ff9800';
      default:
        return '#2196f3';
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const getQualityColor = (score: number) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    return 'error';
  };

  const getQualityHexColor = (score: number) => {
    if (score >= 8) return '#4caf50';
    if (score >= 6) return '#ff9800';
    return '#f44336';
  };

  const getQualityIcon = (score: number) => {
    if (score >= 8) return <CheckCircle sx={{ color: '#4caf50' }} />;
    if (score >= 6) return <Warning sx={{ color: '#ff9800' }} />;
    return <Error sx={{ color: '#f44336' }} />;
  };

  const sentimentColors = {
    positive: '#4caf50',
    neutral: '#ff9800',
    negative: '#f44336',
  };

  const qualityColors = {
    Excellent: '#4caf50',
    Good: '#8bc34a',
    Fair: '#ff9800',
    Poor: '#f44336',
  };

  if (loading) {
    return (
      <div className="page-container text-center">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">
            {t('loadingUserDashboard')}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="alert alert-error">
          <span>{error}</span>
          <button className="btn-secondary" onClick={fetchPerformanceData}>
            <Refresh /> {t('common_refresh')}
          </button>
        </div>
      </div>
    );
  }

  if (!performanceData) {
    return (
      <div className="page-container">
        <div className="alert alert-info">
          {t('noPerformanceDataFound')}
        </div>
      </div>
    );
  }

  const { user_info, basic_metrics, sentiment_distribution, industry_distribution, quality_distribution, performance_trend, top_intents } = performanceData;

  // Prepare chart data
  const sentimentChartData = Object.entries(sentiment_distribution).map(([sentiment, data]) => ({
    name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
    value: data.count,
    color: sentimentColors[sentiment as keyof typeof sentimentColors] || '#9e9e9e',
  }));

 

  const trendChartData = performance_trend.slice(0, 14).reverse().map(item => ({
    date: new Date(item.call_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    calls: item.daily_calls,
    quality: item.daily_avg_quality,
  }));

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
    <div className="page-container">
      {/* Header */}
      <div className="mb-xl flex items-center gap-md">
        <IconButton onClick={() => navigate('/user-list')}>
          <ArrowBack />
        </IconButton>
        <div className={`avatar avatar-${user_info.role}`} style={{width: '64px', height: '64px', fontSize: '1.5rem'}}>
          {getRoleIcon(user_info.role)}
        </div>
        <div className="flex-1">
          <h1 className="page-title">
            {user_info.full_name}
          </h1>
          <div className="flex items-center gap-sm mt-sm">
            <span className={`chip chip-${user_info.role}`}>
              {user_info.role}
            </span>
            <span className="chip chip-secondary">
              {user_info.department}
            </span>
          </div>
        </div>
        <button className="btn-secondary" onClick={fetchPerformanceData}>
          <Refresh style={{marginRight: '8px'}} />
          {t('common_refresh')}
        </button>
      </div>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Phone sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {basic_metrics.total_calls || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('totalCalls')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Star sx={{ fontSize: 40, color: getQualityColor(basic_metrics.avg_quality_score || 0), mb: 1 }} />
              <Typography variant="h4" sx={{ color: getQualityColor(basic_metrics.avg_quality_score || 0) }}>
                {(basic_metrics.avg_quality_score || 0).toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('avgQualityScore')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Schedule sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info">
                {formatDuration(basic_metrics.avg_call_duration || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('avgCallDuration')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success">
                {formatDuration(basic_metrics.total_call_duration || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('totalTalkTime')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('performanceTrendLast14Days')}
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <RechartsTooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="calls" fill="#2196f3" name="Daily Calls" />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="calls"
                      stroke="#4caf50"
                      strokeWidth={3}
                      name="Calls"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('sentimentDistribution')}
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sentimentChartData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {sentimentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
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
                                  primary={file.filename.split("_")[1]}
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
                                        {Array.isArray(analysis.participants) 
                                          ? analysis.participants.join(', ') 
                                          : analysis.participants || 'N/A'}
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
                                        Sentiment
                                      </Typography>
                                      <Typography variant="body2" fontWeight="bold">
                                        
                                      </Typography>
                                   <Chip
  label={analysis.analysis?.sentiment}
  size="small"
  sx={{
    backgroundColor: getSentimentColor(analysis.analysis?.sentiment),
    color: "#fff",
    textTransform: "capitalize"
  }}
/>
                                    </Paper>
                                  </Grid>
                                  
                                  <Grid item xs={6}>
                                    <Paper sx={{ p: 1, textAlign: 'center' }}>
                                      <Psychology sx={{ fontSize: 20, color: 'text.secondary' }} />
                                      <Typography variant="caption" display="block">
                                        {t('intent')}
                                      </Typography>
                                      <Typography variant="body2" fontWeight="bold" sx={{  textTransform: 'capitalize' }}>
                                         
                                        {analysis.analysis?.intents?.[0]?.intent || 'N/A'}
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



       

   
    </div>
  );
};
