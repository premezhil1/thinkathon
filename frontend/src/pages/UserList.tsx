import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Box, 
  Typography,
  Card,
  CardContent,
  Grid,
  Avatar,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Divider, 
  Tooltip,
} from '@mui/material';
import {
  Person,
  Search,
  FilterList, 
  Email, 
  Refresh,
  Dashboard as DashboardIcon,
  AdminPanelSettings,
  SupervisorAccount,
  PersonOutline,
  AccessTime,
  SentimentSatisfied,
  SentimentDissatisfied,
  SentimentNeutral,
  CallMade,
} from '@mui/icons-material';
import axios from 'axios';

interface User {
  userId: string;
  userName: string;
  email: string;
  fullName: string;
  department: string;
  role: string;
  isActive: boolean;
  totalCallDuration: number;
  totalCalls: number;
  positiveCount: number;
  negativeCount: number;
  neutralCount: number;
  createdAt: string;
  updatedAt: string;
}

const formatDuration = (seconds: number): string => {
  if (seconds === 0) return '0m';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

const getSentimentColor = (sentiment: 'positive' | 'negative' | 'neutral'): string => {
  switch (sentiment) {
    case 'positive':
      return '#4caf50';
    case 'negative':
      return '#f44336';
    case 'neutral':
      return '#ff9800';
    default:
      return '#757575';
  }
};

export const UserList: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/users');
      setUsers(response.data.users);
      setFilteredUsers(response.data.users);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    let filtered = users;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(user =>
        user.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply role filter
    if (roleFilter !== 'all') {
      filtered = filtered.filter(user => user.role === roleFilter);
    }

    // Only show active users
    filtered = filtered.filter(user => user.isActive);

    setFilteredUsers(filtered);
  }, [users, searchTerm, roleFilter]);

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

  const handleUserClick = (userId: string) => {
    navigate(`/user-dashboard/${userId}`);
  };

  const uniqueRoles = Array.from(new Set(users.map(user => user.role)));
  if (loading) {
    return (
      <div className="page-container text-center">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">
            {t('userList_loadingUsers')}
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
          <button className="btn-secondary" onClick={fetchUsers}>
            <Refresh /> {t('common_refresh')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container ">
      {/* Header */}
      <div className="user-list-header">
        <div>
          <h1 className="page-title">
            {t('userList_userManagement')}
          </h1>
           
        </div>
        <button className="btn-secondary" onClick={fetchUsers}>
          <Refresh className="user-list-refresh-icon" />
          {t('common_refresh')}
        </button>
      </div>

      {/* Filters */}
      <Paper className="user-list-filters">
        <h3 className="user-list-filter-title">
          <FilterList />
          {t('common_filter')}
        </h3>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label={t('userList_searchUsers')}
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              placeholder={t('userList_searchPlaceholder')}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              select
              label={t('common_role')}
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              SelectProps={{ native: true }}
            >
              <option value="all">{t('userList_allRoles')}</option>
              {uniqueRoles.map(role => (
                <option key={role} value={role}>
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </option>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </Paper> 

      {/* User List */}
      <Card>
        <CardContent>
          <h2 className="user-list-title">
            {t('userList_usersCount', { count: filteredUsers.length })}
          </h2>
          <div className="user-list-divider"></div>
          
          {filteredUsers.length === 0 ? (
            <div className="user-list-empty-state">
              <Person className="user-list-empty-icon" />
              <h3 className="user-list-empty-title">
                {t('userList_noUsersFound')}
              </h3>
              <p className="user-list-empty-subtitle">
                {t('userList_adjustSearchCriteria')}
              </p>
            </div>
                   ) : (
                    <div className="user-list-container">
                      {filteredUsers.map((user) => (
                        <div key={user.userId} className="user-list-item" onClick={() => handleUserClick(user.userId)}>
                          <div className="user-list-avatar">
                            <div className="user-avatar" style={{ backgroundColor: getAvatarColor(user.role) }}>
                              {getRoleIcon(user.role)}
                            </div>
                          </div>
                          <div className="user-list-content">
                            <div className="user-list-primary">
                              <h3 className="user-full-name">{user.fullName}</h3>
                              <span className={`user-role-chip role-${user.role}`}>{user.role}</span>
                            </div>
                            <div className="user-list-secondary">
                              <div className="user-detail-item">
                                <Person className="user-detail-icon" />
                                @{user.userName}
                              </div>
                              <div className="user-detail-item">
                                <Email className="user-detail-icon" />
                                {user.email}
                              </div>
                              <div className="user-call-metrics">
                                <div className="user-metric-chip">
                                  <CallMade className="user-metric-icon" />
                                  {t('userList_callsCount', { count: user.totalCalls })}
                                </div>
                                <div className="user-metric-chip">
                                  <AccessTime className="user-metric-icon" />
                                  {formatDuration(user.totalCallDuration)}
                                </div>
                              </div>
                              {(user.positiveCount > 0 || user.negativeCount > 0 || user.neutralCount > 0) && (
                                <div className="user-sentiment-chips">
                                  {user.positiveCount > 0 && (
                                    <div className="sentiment-chip positive">
                                      <SentimentSatisfied className="sentiment-icon" />
                                      {user.positiveCount}
                                    </div>
                                  )}
                                  {user.negativeCount > 0 && (
                                    <div className="sentiment-chip negative">
                                      <SentimentDissatisfied className="sentiment-icon" />
                                      {user.negativeCount}
                                    </div>
                                  )}
                                  {user.neutralCount > 0 && (
                                    <div className="sentiment-chip neutral">
                                      <SentimentNeutral className="sentiment-icon" />
                                      {user.neutralCount}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="user-list-actions">
                            <button className="btn-icon" title={t('userList_viewDashboard')} onClick={(e) => { e.stopPropagation(); handleUserClick(user.userId); }}>
                              <DashboardIcon />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
        </CardContent>
      </Card>
    </div>
  );
};
