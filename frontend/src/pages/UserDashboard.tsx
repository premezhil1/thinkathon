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
  Person,
  TrendingUp,
  Phone,
  Schedule,
  Star,
  Psychology,
  Business,
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

interface BasicMetrics {
  total_calls: number;
  avg_quality_score: number;
  avg_call_duration: number;
  total_call_duration: number;
  first_call_date: string;
  last_call_date: string;
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

export const UserDashboard: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const qualityChartData = Object.entries(quality_distribution).map(([quality, count]) => ({
    name: quality,
    value: count,
    color: qualityColors[quality as keyof typeof qualityColors] || '#9e9e9e',
  }));

  const industryChartData = Object.entries(industry_distribution).map(([industry, data]) => ({
    industry,
    calls: data.count,
    avgQuality: data.avg_quality,
  }));

  const trendChartData = performance_trend.slice(0, 14).reverse().map(item => ({
    date: new Date(item.call_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    calls: item.daily_calls,
    quality: item.daily_avg_quality,
  }));

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
      </Grid>

      <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('industryPerformance')}
              </Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={industryChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="industry" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <RechartsTooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="calls" fill="#2196f3" name="Calls" />
                    <Bar yAxisId="right" dataKey="avgQuality" fill="#4caf50" name="Avg Quality" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

   
    </div>
  );
};
