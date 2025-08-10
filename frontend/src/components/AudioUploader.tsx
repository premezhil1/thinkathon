import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { useTranslation } from 'react-i18next';
import {
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
  Avatar,
} from '@mui/material';
import { CloudUpload, AudioFile, Person } from '@mui/icons-material';
import axios from 'axios';

interface AudioUploaderProps {
  onUploadSuccess: (analysisId: string) => void;
  onUploadError: (error: string) => void;
}

interface User {
  userId: string;
  userName: string;
  email: string;
  fullName: string;
  department: string;
  role: string;
  isActive: boolean;
}

export const AudioUploader: React.FC<AudioUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [industry, setIndustry] = useState('eCommerce');
  const [userId, setUserId] = useState('agent_001');
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

 

  const { t } = useTranslation();

  const industries = [
    { value: 'eCommerce', label: 'eCommerce' },
    { value: 'Insurance', label: 'Insurance' },
    { value: 'Customer Service', label: 'Customer Service' },
    { value: 'Telecom', label: 'Telecom' },
    { value: 'Healthcare', label: 'Healthcare' },
    { value: 'Travel', label: 'Travel' },
    { value: 'Real Estate', label: 'Real Estate' }
  ]; 

  // Load users from API
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoadingUsers(true);
        const response = await axios.get('/api/users');
        setUsers(response.data.users || []);
      } catch (error) {
        console.error('Failed to load users:', error);
        onUploadError('Failed to load users from server');
      } finally {
        setLoadingUsers(false);
      }
    };

    fetchUsers();
  }, [onUploadError]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('industry', industry);
      formData.append('user_id', userId);

      const response = await axios.post('/api/upload-audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        },
      });

      onUploadSuccess(response.data.analysis_id);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Upload failed';
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [industry, userId, onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3']
    },
    multiple: false,
    disabled: uploading,
  });

  const handleIndustryChange = (event: SelectChangeEvent) => {
    setIndustry(event.target.value);
  };

  const handleUserChange = (event: SelectChangeEvent) => {
    setUserId(event.target.value);
  };

  const selectedUser = users.find(user => user.userId === userId);

  return (
    <div>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{t('upload_selectUser')}</InputLabel>
        <Select
          value={userId}
          label={t('upload_selectUser')}
          onChange={handleUserChange}
          disabled={uploading || loadingUsers}
          renderValue={(value) => {
            const user = users.find(u => u.userId === value);
            return user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
  {(user?.userName?.charAt(0) || '').toUpperCase()}
</Avatar>
                <span>{user.userName}</span>
                <Chip 
                  label={user.role} 
                  size="small" 
                  variant="outlined"
                  sx={{ ml: 1, height: 20 }}
                />
              </div>
            ) : value;
          }}
        >
          {users.map((user) => (
            <MenuItem key={user.userId} value={user.userId}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', width: '100%' }}>
                <Avatar sx={{ width: 32, height: 32 }}>
                  {user?.userName?.charAt(0).toUpperCase()}
                </Avatar>
                <div style={{ flex: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                    {user.userName}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user.fullName} • {user.department}
                  </Typography>
                </div>
                <Chip 
                  label={user.role} 
                  size="small" 
                  color={user.role === 'admin' ? 'error' : user.role === 'manager' ? 'warning' : 'default'}
                  variant="outlined"
                />
              </div>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{t('upload_industry')}</InputLabel>
        <Select
          value={industry}
          label={t('upload_industry')}
          onChange={handleIndustryChange}
          disabled={uploading}
        >
          {industries.map((ind) => (
            <MenuItem key={ind.value} value={ind.value}>
              {ind.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'primary.50' : 'background.paper',
          cursor: uploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: uploading ? 'grey.300' : 'primary.main',
            backgroundColor: uploading ? 'background.paper' : 'primary.50',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          {uploading ? (
            <AudioFile sx={{ fontSize: 48, color: 'primary.main' }} />
          ) : (
            <CloudUpload sx={{ fontSize: 48, color: 'grey.400' }} />
          )}
          
          {uploading ? (
            <div style={{ width: '100%', maxWidth: '300px' }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t('upload_uploading')} {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </div>
          ) : (
            <>
              <Typography variant="h6" color="text.primary">
                {isDragActive ? t('upload_dropFileHere') : t('upload_title')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('upload_dragDropText')}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t('upload_supportedFormats')}
              </Typography>
              <Button variant="outlined" disabled={uploading}>
                {t('upload_chooseFile')}
              </Button>
            </>
          )}
        </div>
      </Paper>

      {acceptedFiles.length > 0 && !uploading && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('upload_selectedFile')} {acceptedFiles[0].name} ({(acceptedFiles[0].size / 1024 / 1024).toFixed(2)} MB)
        </Alert>
      )}
    </div>
  );
};
