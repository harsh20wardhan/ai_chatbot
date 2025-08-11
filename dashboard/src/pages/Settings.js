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
  IconButton,
} from '@mui/material';
import { Save as SaveIcon, Visibility as VisibilityIcon, VisibilityOff as VisibilityOffIcon } from '@mui/icons-material';
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
  // Removed static API keys section
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
      
      await updatePassword(passwordData.newPassword, passwordData.currentPassword);
      
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
  
  // Removed API key handlers
  
  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };
  
  // Removed API key helpers
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h3" component="h1" sx={{ mb: 0.5 }}>
            Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage your profile, password, and notifications
          </Typography>
        </Box>
      </Box>
      
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
          
          {/* Removed API Keys section */}
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