import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import './i18n/i18n'; // Initialize i18n
import { Header } from './components/Header';
import { Homepage } from './pages/Homepage';
import { Upload } from './pages/Upload';
import { AnalysisResults } from './pages/AnalysisResults';
import { AnalysisHistory } from './pages/AnalysisHistory';
import { UserStatus } from './pages/UserStatus';
import { UserList } from './pages/UserList';
import { UserDashboard } from './pages/UserDashboard';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '12px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
          <Header />
          <Routes>
            <Route path="/" element={<Homepage />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/results/:analysisId" element={<AnalysisResults />} />
            <Route path="/history" element={<AnalysisHistory />} />
            <Route path="/user/:userId/status" element={<UserStatus />} />
            <Route path="/user-list" element={<UserList />} />
            <Route path="/user-dashboard/:userId" element={<UserDashboard />} />
          </Routes>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
