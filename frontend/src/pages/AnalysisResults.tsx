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
  Chip,
  Alert,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';
import {
  SentimentSatisfied,
  Psychology,
  AccessTime,
  Person,
} from '@mui/icons-material';
import axios from 'axios';

interface AnalysisData {
  conversation_data: any;
  analysis: any;
  processing_info: any;
  user_info?: {
    user_id: string;
    username: string;
    email: string;
    full_name: string;
    department: string;
    role: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
}

interface IntentDataItem {
  name: string;
  confidence: number;
  color: string;
}

interface TopicDataItem {
  name: string;
  relevance: number;
  color: string;
}
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7f50', '#00bcd4'];

export const AnalysisResults: React.FC = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchResults = async () => {
      if (!analysisId) return;

      try {
        const response = await axios.get(`/api/results/${analysisId}`);
        setData(response.data);
      } catch (error: any) {
        setError(error.response?.data?.detail || 'Failed to load results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [analysisId]);

  if (loading) {
    return (
      <Container maxWidth="lg" className="page-container">
        <div className="mb-lg">
          <h1 className="page-title">
            Analysis Results
          </h1>
          <p className="page-subtitle">
            Comprehensive analysis of conversation
          </p>
        </div>
        <CircularProgress size={40} />
        <Typography variant="h6" className="mt-2">
          Loading analysis results...
        </Typography>
      </Container>
    );
  }

  if (error || !data) {
    return (
      <Container maxWidth="lg" className="page-container">
        <Alert severity="error" className="mt-4">
          {error || 'No data available'}
        </Alert>
      </Container>
    );
  }

  const { conversation_data, analysis, processing_info, user_info } = data;

  const getDuration = () => {
    const duration = processing_info?.duration || conversation_data?.duration || 0;
    return typeof duration === 'number' && !isNaN(duration) && duration > 0 ? duration : 0;
  };

  const getParticipantCount = () => {
    const participants = conversation_data?.participants;
    if (typeof participants === 'number') {
      return participants;
    }
    if (Array.isArray(participants)) {
      return participants.length;
    }
    return 0;
  };

  const ConversationSummary = ({ summary }: { summary: string }) => {
    const conversationId = summary?.match(/Conversation ([\w-]+)/)?.[1] || 'N/A';
    const industry = summary?.match(/\((.*?) industry\)/)?.[1] || 'N/A';
    const primaryIntent = summary?.match(/PRIMARY INTENT: (.*?)\n/)?.[1] || 'N/A';
    const mainTopic = summary?.match(/MAIN TOPIC: (.*?)\n/)?.[1] || 'N/A';
    const sentiment = summary?.match(/OVERALL SENTIMENT: (.*?)\n/)?.[1] || 'N/A';
    const resolution = summary?.match(/RESOLUTION STATUS: (.*?)\n/)?.[1] || 'N/A';
    const finalSummary = summary?.split("RESOLUTION STATUS:")[1]?.split("\n\n")[1] || 'No summary available';

    return (
      <Box className="conversation-summary">
        <Typography variant="body2" className="conversation-summary-industry">
          <strong>Industry:</strong> {industry}
        </Typography>
        <Typography variant="body2" className="conversation-summary-primary-intent">
          <strong>Primary Intent:</strong> {primaryIntent}
        </Typography>
        <Typography variant="body2" className="conversation-summary-main-topic">
          <strong>Main Topic:</strong> {mainTopic}
        </Typography>
        <Typography variant="body2" className="conversation-summary-sentiment">
          <strong>Overall Sentiment:</strong> {sentiment}
        </Typography>
        <Typography variant="body2" className="conversation-summary-resolution">
          <strong>Resolution Status:</strong> {resolution}
        </Typography>
        <Typography variant="body2" className="conversation-summary-final-summary">
          <strong>Summary:</strong> {finalSummary}
        </Typography>
      </Box>
    );
  };

  const getOverallSentiment = () => {
    return analysis.overall_sentiment?.label || 'Unknown';
  };

  const getQualityScore = () => {
    return analysis.quality_score || 0;
  };

  const sentimentData = analysis?.participant_sentiments
    ? Object.entries(analysis.participant_sentiments).map(([name, data]: [string, any]) => ({
      name: name || 'Unknown',
      positive: (data?.sentiment_counts?.positive || 0) ,
      negative: (data?.sentiment_counts?.negative || 0) ,
      neutral: (data?.sentiment_counts?.neutral || 0) ,
    }))
    : [];

  const intentData = analysis?.intents?.map((intent: any, index: number) => ({
    name: intent?.intent || 'Unknown Intent',
    confidence: (intent?.confidence || 0) * 100,
    color: COLORS[index % COLORS.length],
  })) || [];

  const topicScores = (analysis?.topics?.topic_scores ?? {}) as Record<string, number>;

  const topicEntries = Object.entries(topicScores)
    .map(([key, value]) => ({
      name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      relevance: isNaN(value) ? 0 : Math.round((value || 0) * 100),
    }))
    .filter(topic => topic.relevance > 0)
    .sort((a, b) => b.relevance - a.relevance)
    .slice(0, 5);

  const topicData = topicEntries.map((topic, index) => ({
    ...topic,
    color: COLORS[index % COLORS.length],
  }));

  return (
    <div className="page-container">
      <div className="mb-lg">
        <h1 className="page-title">
          Analysis Results
        </h1>
        <p className="page-subtitle">
          Comprehensive analysis of conversation
        </p>
      </div>

      {/* User Information Section */}
      {user_info && (
        <div className="user-info-card">
          <div className="user-info-header">
            <div className={`user-info-avatar ${user_info.role === 'admin' ? 'avatar-admin' :
              user_info.role === 'manager' ? 'avatar-manager' : 'avatar-user'
              }`}>
              {user_info.full_name ? user_info.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="user-info-details">
              <h3 className="user-info-name">
                Uploaded by: {user_info.full_name || user_info.username}
              </h3>
              <div className="user-info-meta">
                <span className={`chip ${user_info.role === 'admin' ? 'chip-admin' : user_info.role === 'manager' ? 'chip-manager' : 'chip-user'}`}>
                  {user_info.role}
                </span>
                <span className="chip chip-primary" style={{ backgroundColor: 'transparent', border: '1px solid var(--primary-color)' }}>
                  {user_info.department}
                </span>
                <span className="text-small color-text-secondary flex items-center gap-xs">
                  <Person style={{ fontSize: '1rem' }} />
                  @{user_info.username}
                </span>
                {user_info.email && (
                  <span className="text-small color-text-secondary">
                    {user_info.email}
                  </span>
                )}
              </div>
            </div>
            <div className="user-info-right">
              <span className="text-caption">
                User ID: {processing_info?.user_id || 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      <Grid container spacing={2}>
        {/* Overview Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <AccessTime className="analysis-card-icon" />
              <Typography variant="h6" className="analysis-card-title">
                Duration
              </Typography>
              <Typography variant="h4" className="analysis-card-value">
                {Math.round(getDuration() / 60)}m
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <Person className="analysis-card-icon" />
              <Typography variant="h6" className="analysis-card-title">
                Participants
              </Typography>
              <Typography variant="h4" className="analysis-card-value">
                {getParticipantCount()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <SentimentSatisfied className="analysis-card-icon" />
              <Typography variant="h6" className="analysis-card-title">
                Overall Sentiment
              </Typography>
              <Chip
                label={getOverallSentiment()}
                color={
                  getOverallSentiment() === 'positive' ? 'success' :
                    getOverallSentiment() === 'negative' ? 'error' : 'default'
                }
                size="small"
                className="analysis-card-chip"
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <Psychology className="analysis-card-icon" />
              <Typography variant="h6" className="analysis-card-title">
                Quality Score
              </Typography>
              <Typography variant="h4" className="analysis-card-value">
                {Math.round(getQualityScore()  )}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Intent Analysis */}
        <Grid item xs={12} sm={6} md={6}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <Typography variant="h6" className="analysis-card-title">
                Intent Analysis
              </Typography>
              {intentData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={intentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, confidence }) => `${name}: ${confidence.toFixed(1)}%`}
                      outerRadius={60}
                      fill="#8884d8"
                      dataKey="confidence"
                    >
                      {intentData.map((entry: IntentDataItem, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="analysis-no-data">
                  No intent data available
                </p>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sentiment Analysis */}
        <Grid item xs={12} sm={6} md={6}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <Typography variant="h6" className="analysis-card-title">
                Participant Sentiment
              </Typography>
              {sentimentData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={sentimentData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number, name: string) => [`${Math.round(value)}`, name]}
                    />
                    <Legend />
                    <Bar dataKey="positive" stackId="a" fill="#4CAF50" />
                    <Bar dataKey="neutral" stackId="a" fill="#FFC107" />
                    <Bar dataKey="negative" stackId="a" fill="#F44336" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="analysis-no-data">
                  No sentiment data available
                </p>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Topic Analysis */}
        <Grid item xs={12} sm={6} md={6}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <Typography variant="h6" className="analysis-card-title">
                Key Topics
              </Typography>
              {topicData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart
                    data={topicData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                    <XAxis
                      dataKey="name"
                      angle={-30}
                      textAnchor="end"
                      interval={0}
                      height={70}
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis
                      domain={[0, 100]}
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip
                      formatter={(value) => `${value}%`}
                      contentStyle={{ fontSize: '13px' }}
                    />
                    <Legend
                      verticalAlign="top"
                      height={30}
                      wrapperStyle={{ fontSize: '13px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="relevance"
                      name="Relevance (%)"
                      stroke="#5b8def"
                      strokeWidth={3}
                      dot={{ fill: '#5b8def', strokeWidth: 2, r: 5 }}
                      activeDot={{ r: 8, fill: '#5b8def' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="analysis-no-data">
                  No topic data available
                </p>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Summary & Insights */}
        <Grid item xs={12} sm={6} md={6}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <h3 className="analysis-card-title">
                Conversation Summary
              </h3>
              <Paper className="conversation-summary-paper">
                {analysis.summary || ''}
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Conversation Summary */}
        <Grid item xs={12}>
          <Card className="analysis-card">
            <CardContent className="analysis-card-content">
              <h3 className="analysis-card-title">
                Full Transcript
              </h3>
              <div className="transcript-container">
                {conversation_data?.dialogue?.map((segment: any, index: number) => {
                  const isAgent = segment?.speaker?.toLowerCase().includes('agent') ||
                    segment?.speaker?.toLowerCase().includes('support') ||
                    segment?.speaker?.toLowerCase().includes('representative');
                  const isCustomer = segment?.speaker?.toLowerCase().includes('customer') ||
                    segment?.speaker?.toLowerCase().includes('caller') ||
                    segment?.speaker?.toLowerCase().includes('user');

                  return (
                    <div
                      key={index}
                      className={`chat-message ${isAgent ? 'agent' : 'customer'}`}
                    >
                      {/* Agent Avatar */}
                      {isAgent && (
                        <div className="chat-avatar agent">
                          <span className="chat-avatar-text">A</span>
                        </div>
                      )}

                      {/* Message Bubble */}
                      <div className="chat-bubble-container">
                        {/* Message Content */}
                        <Paper
                          elevation={1}
                          className={`chat-bubble ${isAgent ? 'agent' : 'customer'}`}
                        >
                          <p className="chat-bubble-text">
                            {segment?.text || 'No text available'}
                          </p>
                        </Paper>

                        {/* Message Info */}
                        <div className={`chat-message-info ${isAgent ? 'agent' : 'customer'}`}>
                          <Chip
                            label={segment?.speaker || 'Unknown'}
                            size="small"
                            color={isAgent ? 'primary' : 'success'}
                            variant="outlined"
                            className={`chat-speaker-chip ${isAgent ? 'agent' : 'customer'}`}
                          />
                          <span className={`chat-timestamp ${isAgent ? 'agent' : 'customer'}`}>
                            {Math.round(segment?.start || 0)}s - {Math.round(segment?.end || 0)}s
                          </span>
                        </div>
                      </div>

                      {/* Customer Avatar */}
                      {isCustomer && (
                        <div className="chat-avatar customer">
                          <span className="chat-avatar-text">C</span>
                        </div>
                      )}
                    </div>
                  );
                }) || (
                  <div className="transcript-empty">
                    <p className="transcript-empty-text">
                      No transcript available
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};
