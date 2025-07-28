import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { Phone, History, Dashboard, CloudUpload, People } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

export const Header: React.FC = () => {
  const location = useLocation();
  const { t } = useTranslation();

  const navItems = [
    { path: '/', label: t('navigation_dashboard'), icon: <Dashboard /> },
    { path: '/upload', label: t('navigation_upload'), icon: <CloudUpload /> },
    { path: '/history', label: t('navigation_history'), icon: <History /> },
    { path: '/user-list', label: t('navigation_users'), icon: <People /> },
  ];

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Phone sx={{ mr: 2 }} />
          <Typography variant="h6" component="div">
            {t('app_name')}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              component={Link}
              to={item.path}
              color="inherit"
              startIcon={item.icon}
              sx={{
                backgroundColor: location.pathname === item.path ? 'rgba(255,255,255,0.1)' : 'transparent',
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
};
