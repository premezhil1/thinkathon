import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Typography,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  Visibility,
  Delete,
  AudioFile,
  AccessTime,
  Person,
  Business,
  Clear,
  FilterList,
} from '@mui/icons-material';
import axios from 'axios';

interface Analysis {
  analysis_id: string;
  processed_at: string;
  source_file: string;
  industry: string;
  duration: number;
  participants: number;
  sentiment: string;
}

interface DeleteDialog {
  open: boolean;
  analysisId: string;
}

export const AnalysisHistory: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [filteredAnalyses, setFilteredAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<DeleteDialog>({ open: false, analysisId: '' });
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Get current date in YYYY-MM-DD format for date inputs
  const getCurrentDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  // Filter states - default to current date
  const [dateFrom, setDateFrom] = useState<string>(getCurrentDate());
  const [dateTo, setDateTo] = useState<string>(getCurrentDate());
  const [industryFilter, setIndustryFilter] = useState<string>('all');

  const fetchAnalyses = async () => {
    try {
      const response = await axios.get('/api/history');
      setAnalyses(response.data.history);
      setFilteredAnalyses(response.data.history);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load analyses');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysesWithFilter = async (fromDate?: string, toDate?: string) => {
    try {
      setLoading(true);
      let url = '/api/history';
      const params = new URLSearchParams();

      if (fromDate) {
        params.append('date_from', fromDate);
      }
      if (toDate) {
        params.append('date_to', toDate);
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await axios.get(url);
      setAnalyses(response.data.history);
      setFilteredAnalyses(response.data.history);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load analyses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  useEffect(() => {
    fetchAnalysesWithFilter(dateFrom, dateTo);
  }, [dateFrom, dateTo]);

  useEffect(() => {
    let filtered = [...analyses];

    // Industry filter
    if (industryFilter !== 'all') {
      filtered = filtered.filter(analysis =>
        analysis.industry === industryFilter
      );
    }

    setFilteredAnalyses(filtered);
  }, [analyses, industryFilter]);

  const clearFilters = () => {
    setDateFrom(getCurrentDate());
    setDateTo(getCurrentDate());
    setIndustryFilter('all');
  };

  const handleViewResults = (analysisId: string) => {
    navigate(`/results/${analysisId}`);
  };

  const handleDeleteClick = (analysisId: string) => {
    setDeleteDialog({ open: true, analysisId });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteDialog.analysisId) return;

    try {
      setDeleteLoading(true);
      await axios.delete(`/api/analysis/${deleteDialog.analysisId}`);
      setAnalyses(analyses.filter(a => a.analysis_id !== deleteDialog.analysisId));
      setDeleteDialog({ open: false, analysisId: '' });
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to delete analysis');
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, analysisId: '' });
  };

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

  const formatDuration = (seconds: number | undefined | null) => {
    // Handle invalid or missing duration values
    if (seconds == null || isNaN(seconds) || seconds < 0) {
      return '0:00';
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="page-container text-center">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">
            {t('loadingAnalysisHistory')}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="analysis-history-header">
        <h1 className="analysis-history-title">
          {t('analysisHistory')}
        </h1>
        <p className="analysis-history-subtitle">
          {t('viewAndManagePastConversationAnalyses')}
        </p>
      </div>

      {/* Filter Controls */}
      <div className="app-card filter-card">
        <div className="app-card-content">
          <div className="filter-header">
            <FilterList />
            <h3 className="card-title">{t('filters')}</h3>
          </div>
          <div className="filter-controls">
            <TextField
              label={t('dateFrom')}
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              InputLabelProps={{ shrink: true }}
              className="filter-field"
            />
            <TextField
              label={t('dateTo')}
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              InputLabelProps={{ shrink: true }}
              className="filter-field"
            />
            <FormControl className="filter-field">
              <InputLabel>{t('industry')}</InputLabel>
              <Select
                value={industryFilter}
                label={t('industry')}
                onChange={(e) => setIndustryFilter(e.target.value as string)}
              >
                <MenuItem value="all">{t('allIndustries')}</MenuItem>
                <MenuItem value="general">{t('general')}</MenuItem>
                <MenuItem value="ecommerce">{t('ecommerce')}</MenuItem>
                <MenuItem value="telecom">{t('telecom')}</MenuItem>
                <MenuItem value="healthcare">{t('healthcare')}</MenuItem>
                <MenuItem value="travel">{t('travel')}</MenuItem>
                <MenuItem value="real_estate">{t('realEstate')}</MenuItem>
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<Clear />}
              onClick={clearFilters}
              className="clear-filters-btn"
            >
              {t('clearFilters')}
            </Button>
          </div>
          {(dateFrom || dateTo || industryFilter !== 'all') && (
            <div className="filter-summary">
              <Typography variant="body2" color="text.secondary">
                {t('showingAnalyses', { count: filteredAnalyses.length, total: analyses.length })}
              </Typography>
            </div>
          )}
        </div>
      </div>

      {error && (
        <Alert severity="error" className="error-alert">
          {error}
        </Alert>
      )}

      {filteredAnalyses.length === 0 ? (
        <div className="app-card">
          <div className="app-card-content empty-state-card">
            <AudioFile className="empty-state-icon" />
            <h3 className="empty-state-title">
              {t('noAnalysesFound')}
            </h3>
            <p className="empty-state-subtitle">
              {t('uploadFirstAudioFileToGetStarted')}
            </p>
            <Button
              variant="contained"
              onClick={() => navigate('/')}
              startIcon={<AudioFile />}
            >
              {t('startNewAnalysis')}
            </Button>
          </div>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid-container grid-4-cols summary-cards-grid">
            <div className="app-card">
              <div className="app-card-content summary-card-content">
                <div className="summary-card-value primary">
                  {filteredAnalyses.length}
                </div>
                <div className="summary-card-label">{t('totalAnalyses')}</div>
              </div>
            </div>

            <div className="app-card">
              <div className="app-card-content summary-card-content">
                <div className="summary-card-value secondary">
                  {Math.round(filteredAnalyses.reduce((sum, a) => sum + a.duration, 0) / 60)}m
                </div>
                <div className="summary-card-label">{t('totalDuration')}</div>
              </div>
            </div>

            <div className="app-card">
              <div className="app-card-content summary-card-content">
                <div className="summary-card-value success">
                  {filteredAnalyses.filter(a => a.sentiment === 'positive').length}
                </div>
                <div className="summary-card-label">{t('positiveCalls')}</div>
              </div>
            </div>

            <div className="app-card">
              <div className="app-card-content summary-card-content">
                <div className="summary-card-value warning">
                  {new Set(filteredAnalyses.map(a => a.industry)).size}
                </div>
                <div className="summary-card-label">{t('industries')}</div>
              </div>
            </div>
          </div>

          {/* Analysis Table */}
          <div className="app-card">
            <div className="app-card-content">
              <h3 className="card-title analysis-table-header">
                {t('recentAnalyses')}
              </h3>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>{t('file')}</TableCell>
                      <TableCell>{t('industry')}</TableCell>
                      <TableCell>{t('duration')}</TableCell>
                      <TableCell>{t('participants')}</TableCell>
                      <TableCell>{t('sentiment')}</TableCell>
                      <TableCell>{t('processed')}</TableCell>
                      <TableCell align="right">{t('actions')}</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredAnalyses.map((analysis) => (
                      <TableRow key={analysis.analysis_id} hover>
                        <TableCell>
                          <div className="table-cell-with-icon">
                            <AudioFile className="table-cell-icon" />
                            <span className="table-cell-text">
                              {analysis.source_file}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={<Business />}
                            label={analysis.industry}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <div className="table-cell-with-icon">
                            <AccessTime className="table-cell-icon small" />
                            {formatDuration(analysis.duration)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="table-cell-with-icon">
                            <Person className="table-cell-icon small" />
                            {analysis.participants}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={analysis.sentiment}
                            size="small"
                            color={getSentimentColor(analysis.sentiment) as any}
                          />
                        </TableCell>
                        <TableCell>
                          <span className="table-cell-secondary">
                            {formatDate(analysis.processed_at)}
                          </span>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            onClick={() => handleViewResults(analysis.analysis_id)}
                            color="primary"
                            size="small"
                          >
                            <Visibility />
                          </IconButton>
                          <IconButton
                            onClick={() => handleDeleteClick(analysis.analysis_id)}
                            color="error"
                            size="small"
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </div>
          </div>
        </>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, analysisId: '' })}
      >
        <DialogTitle>{t('confirmDelete')}</DialogTitle>
        <DialogContent className="delete-dialog-content">
          <Typography className="delete-dialog-text">
            {t('areYouSureYouWantToDeleteThisAnalysis')}
          </Typography>
        </DialogContent>
        <DialogActions className="delete-dialog-actions">
          <Button onClick={() => setDeleteDialog({ open: false, analysisId: '' })}>
            {t('cancel')}
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={deleteLoading}
          >
            {deleteLoading ? <CircularProgress size={20} /> : t('delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
