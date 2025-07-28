import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton, 
  Stack,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Business,
  Assessment,
  Schedule,
  People,
  SentimentSatisfied,
  Star,
  Visibility,
  Analytics,
  Timeline,
  FilterList,
  Refresh,
} from '@mui/icons-material';
import axios from 'axios';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar } from 'recharts';

interface IndustryStats {
  industry: string;
  count: number;
  avg_duration: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
}

interface SentimentStats {
  sentiment: string;
  count: number;
}

interface DailyActivity {
  date: string;
  count: number;
}

interface QualityMetrics {
  avg_quality: number;
  min_quality: number;
  max_quality: number;
  avg_duration: number;
  avg_participants: number;
  total_positive: number;
  total_negative: number;
}

interface RecentActivity {
  analysis_id: string;
  processed_at: string;
  industry: string;
  sentiment: string;
  quality_score: number;
}

interface TopicSentimentData {
  topic: string;
  positive: number;
  neutral: number;
  negative: number;
  totalCount: number;
  total_conversations: number;
}

interface UserPerformanceData {
  user_id: string;
  username: string;
  full_name: string;
  role: string;
  department: string;
  total_calls: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  avg_quality_score: number;
  total_duration: number;
  positive_percentage: number;
  negative_percentage?: number;
  performance_score?: number;
}

interface TopUserPerformance {
  top_positive_sentiment: UserPerformanceData[];
  top_low_negative_sentiment: UserPerformanceData[];
  top_overall_performance: UserPerformanceData[];
}

interface Stats {
  total_analyses: number;
  industry_breakdown: IndustryStats[];
  sentiment_distribution: SentimentStats[];
  daily_activity: DailyActivity[];
  quality_metrics: QualityMetrics;
  recent_activity: RecentActivity[];
  top_user_performance: TopUserPerformance;
}

interface DashboardStats {
  topicSentiments: TopicSentimentData[];
  totalAnalyses: number;
  avgSentimentScore: number;
}

export const Homepage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableIndustries, setAvailableIndustries] = useState<string[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const { t } = useTranslation(); 
  
  // Get current date in YYYY-MM-DD format
  const getCurrentDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };
  
  // Filter states with current date as default
  const [dateFrom, setDateFrom] = useState<string>(getCurrentDate());
  const [dateTo, setDateTo] = useState<string>(getCurrentDate());
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all');
  const [filtersApplied, setFiltersApplied] = useState(false);

  useEffect(() => {
    fetchAvailableIndustries();
    const defaultFilters = {
      dateFrom: getCurrentDate(),
      dateTo: getCurrentDate(),
      industry: 'all'
    };
    // Apply default filters on initial load
    fetchStats(defaultFilters);
    fetchDashboardStats(defaultFilters);
  }, []);

  const fetchAvailableIndustries = async () => {
    try {
      const response = await axios.get('/api/industries');
      setAvailableIndustries(response.data.industries || []);
    } catch (error) {
      console.error('Failed to fetch industries:', error);
    }
  };

  const fetchStats = async (filters?: { dateFrom?: string; dateTo?: string; industry?: string }) => {
    try {
      setLoading(true);
      setError(null); // Clear any previous errors
      const params = new URLSearchParams();
      
      if (filters?.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters?.dateTo) params.append('date_to', filters.dateTo);
      if (filters?.industry && filters.industry !== 'all') params.append('industry', filters.industry);
      
      const url = `/api/stats${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await axios.get(url);
      
      // Ensure the response has the expected structure
      const statsData = response.data || {};
      
      // Provide default values for missing properties
      const normalizedStats = {
        total_analyses: statsData.total_analyses || 0,
        industry_breakdown: Array.isArray(statsData.industry_breakdown) ? statsData.industry_breakdown : [],
        sentiment_distribution: Array.isArray(statsData.sentiment_distribution) ? statsData.sentiment_distribution : [],
        daily_activity: Array.isArray(statsData.daily_activity) ? statsData.daily_activity : [],
        quality_metrics: {
          avg_quality: statsData.quality_metrics?.avg_quality || 0,
          min_quality: statsData.quality_metrics?.min_quality || 0,
          max_quality: statsData.quality_metrics?.max_quality || 0,
          avg_duration: statsData.quality_metrics?.avg_duration || 0,
          avg_participants: statsData.quality_metrics?.avg_participants || 0,
          total_positive: statsData.quality_metrics?.total_positive || 0,
          total_negative: statsData.quality_metrics?.total_negative || 0,
          ...statsData.quality_metrics
        },
        recent_activity: Array.isArray(statsData.recent_activity) ? statsData.recent_activity : [],
        top_user_performance: {
          top_positive_sentiment: Array.isArray(statsData.top_user_performance?.top_positive_sentiment) ? statsData.top_user_performance.top_positive_sentiment : [],
          top_low_negative_sentiment: Array.isArray(statsData.top_user_performance?.top_low_negative_sentiment) ? statsData.top_user_performance.top_low_negative_sentiment : [],
          top_overall_performance: Array.isArray(statsData.top_user_performance?.top_overall_performance) ? statsData.top_user_performance.top_overall_performance : [],
        },
        ...statsData
      };
      
      setStats(normalizedStats);
      setFiltersApplied(!!(filters?.dateFrom || filters?.dateTo || (filters?.industry && filters.industry !== 'all')));
    } catch (error: any) {
      console.error('Error fetching stats:', error);
      setError(error.response?.data?.error || 'Failed to load statistics');
      // Set empty stats on error to prevent undefined access
      setStats({
        total_analyses: 0,
        industry_breakdown: [],
        sentiment_distribution: [],
        daily_activity: [],
        quality_metrics: {
          avg_quality: 0,
          min_quality: 0,
          max_quality: 0,
          avg_duration: 0,
          avg_participants: 0,
          total_positive: 0,
          total_negative: 0
        },
        recent_activity: [],
        top_user_performance: {
          top_positive_sentiment: [],
          top_low_negative_sentiment: [],
          top_overall_performance: []
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardStats = async (filters?: { dateFrom?: string; dateTo?: string; industry?: string }) => {
    try {
      setStatsLoading(true);
      const params = new URLSearchParams();
      
      if (filters?.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters?.dateTo) params.append('date_to', filters.dateTo);
      if (filters?.industry && filters.industry !== 'all') params.append('industry', filters.industry);
      
      const url = `/api/dashboard/topic-sentiments${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await axios.get(url);
      setDashboardStats(response.data);
    } catch (err: any) {
      console.error('Failed to fetch dashboard stats:', err);
    } finally {
      setStatsLoading(false);
    }
  }; 

  const handleApplyFilters = () => {
    const filters = {
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
      industry: selectedIndustry
    };
    fetchStats(filters);
    fetchDashboardStats(filters);
  };

  const handleClearFilters = () => {
    setDateFrom('');
    setDateTo('');
    setSelectedIndustry('all');
    fetchStats();
    fetchDashboardStats();
  };

  const handleIndustryChange = (event: SelectChangeEvent) => {
    setSelectedIndustry(event.target.value);
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString();
  };

  const getSentimentColor = (sentiment: string): string => {
    switch (sentiment.toLowerCase()) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      case 'neutral': return '#ff9800';
      case 'concerned': return '#ff5722';
      case 'frustrated': return '#e91e63';
      default: return '#9e9e9e';
    }
  };

  const getIndustryIcon = (industry: string) => {
    switch (industry.toLowerCase()) {
      case 'healthcare': return '🏥';
      case 'finance': return '💰';
      case 'retail': return '🛒';
      case 'insurance': return '🛡️';
      case 'technology': return '💻';
      case 'education': return '📚';
      default: return '🏢';
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="homepage-loading">
          <CircularProgress />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <Alert severity="error">{error}</Alert>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="page-container">
        <Alert severity="info">No data available</Alert>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="mb-lg">
        <h1 className="page-title">
          Call Analyzer Dashboard
        </h1>
        <p className="page-subtitle">
          Comprehensive analytics across all industries
        </p>
      </div>

      {/* Filter Section */}
      <Card className="homepage-filter-card">
        <CardContent>
          <div className="filter-header">
            <FilterList className="filter-icon" />
            <Typography variant="h6" gutterBottom>
              Filters
            </Typography>
            {filtersApplied && (
              <Chip 
                label="Filters Applied" 
                color="primary" 
                size="small" 
                className="filter-applied-chip"
              />
            )}
          </div>
          <Grid container spacing={2} alignItems="end">
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                label="Date From"
                type="date"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
                fullWidth
                size="small"
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2.5}>
              <TextField
                label="Date To"
                type="date"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
                fullWidth
                size="small"
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel id="industry-select-label" className="filter-input-small">Industry</InputLabel>
                <Select
                  labelId="industry-select-label"
                  value={selectedIndustry}
                  label="Industry"
                  onChange={handleIndustryChange}
                  className="filter-select-small"
                >
                  <MenuItem value="all" className="filter-menu-item">All Industries</MenuItem>
                  {availableIndustries.map((industry) => (
                    <MenuItem key={industry} value={industry} className="filter-menu-item">
                      {getIndustryIcon(industry)} {industry}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Stack direction="row" spacing={1}>
                <Button 
                  variant="contained" 
                  onClick={handleApplyFilters}
                  startIcon={<Analytics className="filter-button-icon" />}
                  disabled={loading}
                  size="small"
                  className="filter-button"
                >
                  Apply
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={handleClearFilters}
                  startIcon={<Refresh className="filter-button-icon" />}
                  disabled={loading}
                  size="small"
                  className="filter-button-clear"
                >
                  Clear
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Key Metrics Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '12px !important' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                    Total Analyses
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#1976d2' }}>
                    {stats?.total_analyses?.toLocaleString() || 0}
                  </Typography>
                </Box>
                <Assessment sx={{ fontSize: '2rem', color: '#1976d2', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '12px !important' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                    Positive Count
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#4caf50' }}>
                    {stats?.quality_metrics?.total_positive?.toLocaleString() || 0}
                  </Typography>
                </Box>
                <SentimentSatisfied sx={{ fontSize: '2rem', color: '#4caf50', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '12px !important' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                    Negative Count
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#f44336' }}>
                    {stats?.quality_metrics?.total_negative?.toLocaleString() || 0}
                  </Typography>
                </Box>
                <Star sx={{ fontSize: '2rem', color: '#f44336', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '12px !important' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                    Avg Duration
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#ff9800' }}>
                    {formatDuration(stats?.quality_metrics?.avg_duration || 0)}
                  </Typography>
                </Box>
                <Schedule sx={{ fontSize: '2rem', color: '#ff9800', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '12px !important' }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                    Avg Participants
                  </Typography>
                  <Typography variant="h4" component="div" sx={{ fontSize: '1.5rem', fontWeight: 600, color: '#9c27b0' }}>
                    {stats?.quality_metrics?.avg_participants?.toFixed(1) || 0}
                  </Typography>
                </Box>
                <People sx={{ fontSize: '2rem', color: '#9c27b0', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Industry and Sentiment Analysis */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '16px !important' }}>
              <Box display="flex" alignItems="center" mb={2}>
                <Business sx={{ mr: 1, fontSize: '1.25rem' }} />
                <Typography variant="h6" component="h2" sx={{ fontSize: '1rem', fontWeight: 500 }}>
                  Industry Breakdown
                </Typography>
              </Box>
              {stats?.industry_breakdown && stats.industry_breakdown.length > 0 ? (
                <TableContainer component={Paper} elevation={0} sx={{ maxHeight: 300 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontSize: '0.75rem', fontWeight: 600, padding: '6px 8px' }}>Industry</TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.75rem', fontWeight: 600, padding: '6px 8px' }}>Count</TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.75rem', fontWeight: 600, padding: '6px 8px' }}>Positive</TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.75rem', fontWeight: 600, padding: '6px 8px' }}>Neutral</TableCell>
                        <TableCell align="right" sx={{ fontSize: '0.75rem', fontWeight: 600, padding: '6px 8px' }}>Negative</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.industry_breakdown.slice(0, 5).map((industry) => (
                        <TableRow key={industry.industry}>
                          <TableCell component="th" scope="row" sx={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                            {getIndustryIcon(industry.industry)} {industry.industry}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                            {industry.count}
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#4caf50', fontWeight: 500 }}>
                              {industry.positive_count || 0}
                            </Typography>
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#ff9800', fontWeight: 500 }}>
                              {industry.neutral_count || 0}
                            </Typography>
                          </TableCell>
                          <TableCell align="right" sx={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                            <Typography variant="body2" sx={{ fontSize: '0.75rem', color: '#f44336', fontWeight: 500 }}>
                              {industry.negative_count || 0}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                  No industry data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ padding: '16px !important' }}>
              <Box display="flex" alignItems="center" mb={2}>
                <SentimentSatisfied sx={{ mr: 1, fontSize: '1.25rem' }} />
                <Typography variant="h6" component="h2" sx={{ fontSize: '1rem', fontWeight: 500 }}>
                  Sentiment Distribution
                </Typography>
              </Box>
              {stats?.sentiment_distribution && stats.sentiment_distribution.length > 0 ? (
                <Stack spacing={1}>
                  {stats.sentiment_distribution.map((sentiment) => (
                    <Box key={sentiment.sentiment}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                        <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 500 }}>
                          {sentiment.sentiment}
                        </Typography>
                        <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                          {sentiment.count}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(sentiment.count / (stats?.total_analyses || 1)) * 100}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: '#f5f5f5',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getSentimentColor(sentiment.sentiment),
                            borderRadius: 3,
                          },
                        }}
                      />
                    </Box>
                  ))}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                  No sentiment data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <div className="homepage-section-header">
                <h3 className="homepage-section-title">
                  <Timeline />
                  Recent Activity
                </h3>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => navigate('/history')}
                  startIcon={<Analytics />}
                >
                  View All History
                </Button>
              </div>
              <TableContainer component={Paper} variant="outlined">
                <Table className="recent-activity-table">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Industry</TableCell>
                      <TableCell>Sentiment</TableCell>
                      <TableCell align="right">Quality Score</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats.recent_activity.map((activity) => (
                      <TableRow key={activity.analysis_id}>
                        <TableCell>
                          <span className="text-body2">
                            {formatDate(activity.processed_at)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <div className="recent-activity-cell-content">
                            <span className="recent-activity-industry-icon text-body2">
                              {getIndustryIcon(activity.industry)}
                            </span>
                            <span className="text-body2 recent-activity-industry-text">
                              {activity.industry}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={activity.sentiment}
                            size="small"
                            className={`recent-activity-sentiment-chip sentiment-chip-${activity.sentiment.toLowerCase()}`}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <div className="recent-activity-quality-container">
                            <span className="text-body2 recent-activity-quality-score">
                              {activity.quality_score}
                            </span>
                            <LinearProgress 
                              variant="determinate" 
                              value={activity.quality_score * 100}
                              className="recent-activity-quality-progress"
                            />
                          </div>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton 
                            size="small"
                            onClick={() => navigate(`/results/${activity.analysis_id}`)}
                          >
                            <Visibility />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid> 
       
      </Grid>


       {/* Top User Performance Section */}
       {!loading && stats?.top_user_performance && (
                <div className="mt-xl">
                  <h2 className="section-title">
                    <People className="section-title-icon" />
                    Top User Performance
                  </h2>
                  
                  <div className="grid-container grid-3-cols">
                    {/* Top Positive Sentiment Users */}
                    <div className="app-card">
                      <div className="app-card-content">
                        <h3 className="card-title">
                          🏆 Top Positive Sentiment
                        </h3>
                        <div className="flex flex-col gap-sm">
                          {stats.top_user_performance.top_positive_sentiment.map((user, index) => (
                            <div key={user.user_id} className="app-card" style={{backgroundColor: '#f0f8f0', border: '1px solid #4CAF50'}}>
                              <div className="p-sm">
                                <div className="flex justify-between items-center mb-xs">
                                  <div className="flex items-center gap-xs">
                                    <span className="chip" style={{
                                      backgroundColor: index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#4CAF50',
                                      color: 'white',
                                      fontSize: 'var(--font-size-xs)',
                                      fontWeight: 'bold'
                                    }}>
                                      #{index + 1}
                                    </span>
                                    <h4 style={{fontSize: 'var(--font-size-sm)', fontWeight: 600, margin: 0}}>
                                      {user.full_name}
                                    </h4>
                                  </div>
                                  <span className="chip" style={{
                                    backgroundColor: user.role === 'admin' ? '#f44336' : user.role === 'manager' ? '#ff9800' : '#2196f3',
                                    color: 'white',
                                    fontSize: 'var(--font-size-xs)'
                                  }}>
                                    {user.role}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center mb-xs">
                                  <span style={{fontSize: 'var(--font-size-xs)', color: '#666'}}>
                                    @{user.username} • {user.department}
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#4CAF50', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    {user.positive_percentage}% Positive
                                  </span>
                                </div>
                                <div className="flex gap-xs">
                                  <span className="chip chip-secondary" style={{fontSize: 'var(--font-size-xs)'}}>
                                    {user.total_calls} calls
                                  </span>
                                  
                                  <span className="chip" style={{backgroundColor: '#4CAF50', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    +{user.positive_count}
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#f44336', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    -{user.negative_count}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Top Low Negative Sentiment Users */}
                    <div className="app-card">
                      <div className="app-card-content">
                        <h3 className="card-title">
                          🛡️ Lowest Negative Sentiment
                        </h3>
                        <div className="flex flex-col gap-sm">
                          {stats.top_user_performance.top_low_negative_sentiment.map((user, index) => (
                            <div key={user.user_id} className="app-card" style={{backgroundColor: '#f8f0f0', border: '1px solid #2196F3'}}>
                              <div className="p-sm">
                                <div className="flex justify-between items-center mb-xs">
                                  <div className="flex items-center gap-xs">
                                    <span className="chip" style={{
                                      backgroundColor: index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#2196F3',
                                      color: 'white',
                                      fontSize: 'var(--font-size-xs)',
                                      fontWeight: 'bold'
                                    }}>
                                      #{index + 1}
                                    </span>
                                    <h4 style={{fontSize: 'var(--font-size-sm)', fontWeight: 600, margin: 0}}>
                                      {user.full_name}
                                    </h4>
                                  </div>
                                  <span className="chip" style={{
                                    backgroundColor: user.role === 'admin' ? '#f44336' : user.role === 'manager' ? '#ff9800' : '#2196f3',
                                    color: 'white',
                                    fontSize: 'var(--font-size-xs)'
                                  }}>
                                    {user.role}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center mb-xs">
                                  <span style={{fontSize: 'var(--font-size-xs)', color: '#666'}}>
                                    @{user.username} • {user.department}
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#2196F3', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    {user.negative_percentage}% Negative
                                  </span>
                                </div>
                                <div className="flex gap-xs">
                                  <span className="chip chip-secondary" style={{fontSize: 'var(--font-size-xs)'}}>
                                    {user.total_calls} calls
                                  </span>
                                   
                                  <span className="chip" style={{backgroundColor: '#4CAF50', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    +{user.positive_count}
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#f44336', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    -{user.negative_count}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Top Overall Performance Users */}
                    <div className="app-card">
                      <div className="app-card-content">
                        <h3 className="card-title">
                          🌟 Top Overall Performance
                        </h3>
                        <div className="flex flex-col gap-sm">
                          {stats.top_user_performance.top_overall_performance.map((user, index) => (
                            <div key={user.user_id} className="app-card" style={{backgroundColor: '#fff8e1', border: '1px solid #FF9800'}}>
                              <div className="p-sm">
                                <div className="flex justify-between items-center mb-xs">
                                  <div className="flex items-center gap-xs">
                                    <span className="chip" style={{
                                      backgroundColor: index === 0 ? '#FFD700' : index === 1 ? '#C0C0C0' : index === 2 ? '#CD7F32' : '#FF9800',
                                      color: 'white',
                                      fontSize: 'var(--font-size-xs)',
                                      fontWeight: 'bold'
                                    }}>
                                      #{index + 1}
                                    </span>
                                    <h4 style={{fontSize: 'var(--font-size-sm)', fontWeight: 600, margin: 0}}>
                                      {user.full_name}
                                    </h4>
                                  </div>
                                  <span className="chip" style={{
                                    backgroundColor: user.role === 'admin' ? '#f44336' : user.role === 'manager' ? '#ff9800' : '#2196f3',
                                    color: 'white',
                                    fontSize: 'var(--font-size-xs)'
                                  }}>
                                    {user.role}
                                  </span>
                                </div>
                                <div className="flex justify-between items-center mb-xs">
                                  <span style={{fontSize: 'var(--font-size-xs)', color: '#666'}}>
                                    @{user.username} • {user.department}
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#FF9800', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    Score: {user.performance_score}
                                  </span>
                                </div>
                                <div className="flex gap-xs">
                                  <span className="chip chip-secondary" style={{fontSize: 'var(--font-size-xs)'}}>
                                    {user.total_calls} calls
                                  </span>
                                  
                                  <span className="chip" style={{backgroundColor: '#4CAF50', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    {user.positive_percentage}% +
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#FFC107', color: 'black', fontSize: 'var(--font-size-xs)'}}>
                                    {user.neutral_count} neutral
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

       {!statsLoading && dashboardStats && (
                <div className="mt-xl">
                 
      
                  <div className="grid-container grid-2-cols">
                    {/* Topic Sentiment Bar Chart */}
                    <div className="app-card">
                      <div className="app-card-content">
                        <h3 className="card-title">
                          Sentiment by Topic
                        </h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={dashboardStats.topicSentiments}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="topic" 
                              angle={-45} 
                              textAnchor="end" 
                              height={80}
                              tick={{ fontSize: 12 }}
                            />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip 
  formatter={(value: number, topic?: string) => [
    `${value}%`, 
    topic ? topic.charAt(0).toUpperCase() + topic.slice(1) : ''
  ]}
/>
                            <Legend />
                            <Bar dataKey="positive" stackId="a" fill="#4CAF50" name="Positive" />
                            <Bar dataKey="neutral" stackId="a" fill="#FFC107" name="Neutral" />
                            <Bar dataKey="negative" stackId="a" fill="#F44336" name="Negative" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
      
                    {/* Topic Statistics */}
                    <div className="app-card">
                      <div className="app-card-content">
                        <h3 className="card-title">
                          Topic Statistics
                        </h3>
                        <div className="flex flex-col gap-md">
                          {dashboardStats.topicSentiments.map((topic, index) => (
                            <div key={index} className="app-card" style={{backgroundColor: '#f8f9fa', border: '1px solid #e9ecef'}}>
                              <div className="p-sm">
                                <div className="flex justify-between items-center mb-xs">
                                  <h4 style={{fontSize: 'var(--font-size-sm)', fontWeight: 600, margin: 0}}>
                                    {topic.topic}
                                  </h4>
                                  <span className="chip chip-secondary" style={{fontSize: 'var(--font-size-xs)'}}>
                                    {topic.total_conversations} calls
                                  </span>
                                </div>
                                <div className="flex gap-xs">
                                  <span className="chip" style={{backgroundColor: '#4CAF50', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    {topic.positive}% Positive
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#FFC107', color: 'black', fontSize: 'var(--font-size-xs)'}}>
                                    {topic.neutral}% Neutral
                                  </span>
                                  <span className="chip" style={{backgroundColor: '#F44336', color: 'white', fontSize: 'var(--font-size-xs)'}}>
                                    {topic.negative}% Negative
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
      
               
                </div>
              )}
             
    </div>
  );
};
