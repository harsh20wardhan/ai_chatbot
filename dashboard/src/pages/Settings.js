import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  TextField,
  Button,
  Grid,
  Avatar,
  Switch,
  FormControlLabel,
  CircularProgress,
  Snackbar,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
} from '@mui/material';
import {
  Save as SaveIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

export default function Settings() {
  const { user, updatePassword } = useAuth();
  
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState({
    currentPassword: false,
    newPassword: false,
    confirmPassword: false,
  });
  const [notifications, setNotifications] = useState({
    email: true,
    bot: true,
    security: true,
  });
  const [apiKeys, setApiKeys] = useState([
    { id: '1', name: 'Development', key: 'sk_test_123456789', created: '2023-05-01T12:00:00Z' },
    { id: '2', name: 'Production', key: 'sk_live_987654321', created: '2023-05-02T14:30:00Z' },
  ]);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });
  
  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.user_metadata?.name || '',
        email: user.email || '',
      });
    }
  }, [user]);
  
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value,
    }));
  };
  
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value,
    }));
  };
  
  const handleTogglePasswordVisibility = (field) => {
    setShowPassword(prev => ({
      ...prev,
      [field]: !prev[field],
    }));
  };
  
  const handleNotificationChange = (e) => {
    const { name, checked } = e.target;
    setNotifications(prev => ({
      ...prev,
      [name]: checked,
    }));
  };
  
  const handleSaveProfile = async () => {
    try {
      setLoading(true);
      
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSnackbar({
        open: true,
        message: 'Profile updated successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error updating profile:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update profile',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleChangePassword = async () => {
    // Validate passwords
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setSnackbar({
        open: true,
        message: 'Passwords do not match',
        severity: 'error',
      });
      return;
    }
    
    if (passwordData.newPassword.length < 6) {
      setSnackbar({
        open: true,
        message: 'Password must be at least 6 characters long',
        severity: 'error',
      });
      return;
    }
    
    try {
      setLoading(true);
      
      await updatePassword(passwordData.newPassword);
      
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      
      setSnackbar({
        open: true,
        message: 'Password changed successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error changing password:', error);
      setSnackbar({
        open: true,
        message: 'Failed to change password',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveNotifications = async () => {
    try {
      setLoading(true);
      
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSnackbar({
        open: true,
        message: 'Notification settings updated successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error updating notification settings:', error);
      setSnackbar({
        open: true,
        message: 'Failed to update notification settings',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleCreateApiKey = async () => {
    try {
      setLoading(true);
      
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const newKey = {
        id: Date.now().toString(),
        name: 'New Key',
        key: `sk_${Math.random().toString(36).substring(2, 15)}`,
        created: new Date().toISOString(),
      };
      
      setApiKeys(prev => [...prev, newKey]);
      
      setSnackbar({
        open: true,
        message: 'API key created successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error creating API key:', error);
      setSnackbar({
        open: true,
        message: 'Failed to create API key',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeleteApiKey = async (id) => {
    try {
      setLoading(true);
      
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setApiKeys(prev => prev.filter(key => key.id !== id));
      
      setSnackbar({
        open: true,
        message: 'API key deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error deleting API key:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete API key',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };
  
  const maskApiKey = (key) => {
    return `${key.substring(0, 7)}...${key.substring(key.length - 4)}`;
  };
  
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={4}>
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Profile Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Avatar
                sx={{ width: 80, height: 80, mr: 2 }}
                alt={profileData.name}
                src="/static/images/avatar.jpg"
              >
                {profileData.name.charAt(0)}
              </Avatar>
              <Box>
                <Typography variant="h6">{profileData.name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {profileData.email}
                </Typography>
              </Box>
            </Box>
            
            <TextField
              fullWidth
              label="Name"
              name="name"
              value={profileData.name}
              onChange={handleProfileChange}
              margin="normal"
              variant="outlined"
            />
            
            <TextField
              fullWidth
              label="Email"
              name="email"
              value={profileData.email}
              onChange={handleProfileChange}
              margin="normal"
              variant="outlined"
              disabled
            />
            
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveProfile}
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Changes'}
            </Button>
          </Paper>
          
          {/* Password Settings */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Change Password
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <TextField
              fullWidth
              label="Current Password"
              name="currentPassword"
              type={showPassword.currentPassword ? 'text' : 'password'}
              value={passwordData.currentPassword}
              onChange={handlePasswordChange}
              margin="normal"
              variant="outlined"
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => handleTogglePasswordVisibility('currentPassword')}
                    edge="end"
                  >
                    {showPassword.currentPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                ),
              }}
            />
            
            <TextField
              fullWidth
              label="New Password"
              name="newPassword"
              type={showPassword.newPassword ? 'text' : 'password'}
              value={passwordData.newPassword}
              onChange={handlePasswordChange}
              margin="normal"
              variant="outlined"
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => handleTogglePasswordVisibility('newPassword')}
                    edge="end"
                  >
                    {showPassword.newPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                ),
              }}
            />
            
            <TextField
              fullWidth
              label="Confirm New Password"
              name="confirmPassword"
              type={showPassword.confirmPassword ? 'text' : 'password'}
              value={passwordData.confirmPassword}
              onChange={handlePasswordChange}
              margin="normal"
              variant="outlined"
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => handleTogglePasswordVisibility('confirmPassword')}
                    edge="end"
                  >
                    {showPassword.confirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                ),
              }}
            />
            
            <Button
              variant="contained"
              onClick={handleChangePassword}
              disabled={loading || !passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Change Password'}
            </Button>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {/* Notification Settings */}
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Notification Settings
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <FormControlLabel
              control={
                <Switch
                  checked={notifications.email}
                  onChange={handleNotificationChange}
                  name="email"
                  color="primary"
                />
              }
              label="Email Notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive email notifications about account activity and updates.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={notifications.bot}
                  onChange={handleNotificationChange}
                  name="bot"
                  color="primary"
                />
              }
              label="Bot Activity Notifications"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive notifications about bot activity and performance.
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={notifications.security}
                  onChange={handleNotificationChange}
                  name="security"
                  color="primary"
                />
              }
              label="Security Alerts"
            />
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
              Receive notifications about security events and login attempts.
            </Typography>
            
            <Button
              variant="contained"
              onClick={handleSaveNotifications}
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Preferences'}
            </Button>
          </Paper>
          
          {/* API Keys */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              API Keys
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Manage your API keys for programmatic access to the platform.
            </Typography>
            
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent sx={{ p: 0 }}>
                <List>
                  {apiKeys.map((key) => (
                    <React.Fragment key={key.id}>
                      <ListItem>
                        <ListItemText
                          primary={key.name}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                {maskApiKey(key.key)}
                              </Typography>
                              <br />
                              Created: {formatDate(key.created)}
                            </>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleDeleteApiKey(key.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                      <Divider />
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
            
            <Button
              variant="outlined"
              onClick={handleCreateApiKey}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Create New API Key'}
            </Button>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}