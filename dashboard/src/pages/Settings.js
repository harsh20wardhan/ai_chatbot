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
  
  // Enhanced crawling settings
  const [crawlingSettings, setCrawlingSettings] = useState({
    default_max_pages: 100,
    default_max_depth: 5,
    default_delay_between_requests: 1.0,
    default_respect_robots_txt: true,
    default_exclude_patterns: '/admin, /api, /private',
    default_include_patterns: '',
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
    
    // Load crawling settings from localStorage
    const savedCrawlingSettings = localStorage.getItem('defaultCrawlingSettings');
    if (savedCrawlingSettings) {
      try {
        setCrawlingSettings(JSON.parse(savedCrawlingSettings));
      } catch (error) {
        console.error('Failed to parse saved crawling settings:', error);
      }
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

  const handleCrawlingSettingChange = (field, value) => {
    setCrawlingSettings(prev => ({
      ...prev,
      [field]: value
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
      setSnackbar({
        open: true,
        message: 'Failed to update profile',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCrawlingSettings = async () => {
    try {
      setLoading(true);
      
      // Save crawling settings to localStorage for now
      localStorage.setItem('defaultCrawlingSettings', JSON.stringify(crawlingSettings));
      
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSnackbar({
        open: true,
        message: 'Crawling settings saved successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to save crawling settings',
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
        
        {/* Enhanced Crawling Settings */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" gutterBottom>
              Enhanced Crawling Settings
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure default options for website crawling. These settings will be used as defaults when starting new crawl jobs.
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Grid container spacing={3}>
              {/* Max Pages and Depth */}
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Maximum Pages"
                  type="number"
                  value={crawlingSettings.default_max_pages}
                  onChange={(e) => handleCrawlingSettingChange('default_max_pages', parseInt(e.target.value) || 100)}
                  inputProps={{ min: 1, max: 1000 }}
                  helperText="Default maximum pages to crawl (1-1000)"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Maximum Depth"
                  type="number"
                  value={crawlingSettings.default_max_depth}
                  onChange={(e) => handleCrawlingSettingChange('default_max_depth', parseInt(e.target.value) || 5)}
                  inputProps={{ min: 1, max: 10 }}
                  helperText="Default link depth for crawling (1-10 levels)"
                  variant="outlined"
                />
              </Grid>
              
              {/* Pattern Filters */}
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Exclude Patterns"
                  placeholder="/admin, /api, /private"
                  value={crawlingSettings.default_exclude_patterns}
                  onChange={(e) => handleCrawlingSettingChange('default_exclude_patterns', e.target.value)}
                  helperText="Default URL patterns to exclude from crawling"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Include Patterns"
                  placeholder="/blog, /docs, /articles"
                  value={crawlingSettings.default_include_patterns}
                  onChange={(e) => handleCrawlingSettingChange('default_include_patterns', e.target.value)}
                  helperText="Default URL patterns to include in crawling (optional)"
                  variant="outlined"
                />
              </Grid>
              
              {/* Advanced Options */}
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Delay Between Requests (seconds)"
                  type="number"
                  value={crawlingSettings.default_delay_between_requests}
                  onChange={(e) => handleCrawlingSettingChange('default_delay_between_requests', parseFloat(e.target.value) || 1.0)}
                  inputProps={{ min: 0.1, max: 10, step: 0.1 }}
                  helperText="Default delay to be respectful to servers"
                  variant="outlined"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', height: '100%', pt: 1 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                    Default Respect robots.txt:
                  </Typography>
                  <Button
                    variant={crawlingSettings.default_respect_robots_txt ? "contained" : "outlined"}
                    size="small"
                    onClick={() => handleCrawlingSettingChange('default_respect_robots_txt', !crawlingSettings.default_respect_robots_txt)}
                    color={crawlingSettings.default_respect_robots_txt ? "success" : "default"}
                  >
                    {crawlingSettings.default_respect_robots_txt ? "Yes" : "No"}
                  </Button>
                </Box>
              </Grid>
            </Grid>
            
            {/* Information Box */}
            <Box sx={{ mt: 3, p: 2, bgcolor: 'info.50', borderRadius: 1, border: '1px solid', borderColor: 'info.200' }}>
              <Typography variant="body2" color="info.700">
                <strong>Enhanced Crawling Features:</strong>
                <br />• Deep crawling with configurable depth control
                <br />• Smart content extraction and noise filtering
                <br />• Robots.txt compliance and rate limiting
                <br />• Pattern-based URL filtering for targeted crawling
                <br />• These settings will be used as defaults for new crawl jobs
              </Typography>
            </Box>
            
            <Button
              variant="contained"
              onClick={handleSaveCrawlingSettings}
              disabled={loading}
              startIcon={<SaveIcon />}
              sx={{ mt: 3 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Crawling Settings'}
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