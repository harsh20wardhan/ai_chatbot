import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControl,
  FormControlLabel,
  FormLabel,
  Radio,
  RadioGroup,
  Switch,
  Card,
  CardContent,
  Grid,
  Divider,
  CircularProgress,
  Snackbar,
  Alert,
  Paper,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from '@mui/material';
import { ChromePicker } from 'react-color';
import {
  ContentCopy as CopyIcon,
  Check as CheckIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { botApi, widgetApi } from '../services/api';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`widget-tabpanel-${index}`}
      aria-labelledby={`widget-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function WidgetConfig() {
  const { botId } = useParams();
  const navigate = useNavigate();
  
  const [tabValue, setTabValue] = useState(0);
  const [bot, setBot] = useState(null);
  const [config, setConfig] = useState({
    theme: 'light',
    primary_color: '#3f51b5',
    position: 'bottom-right',
    welcome_message: '',
    placeholder_text: 'Ask me anything...',
    show_sources: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [colorPickerOpen, setColorPickerOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch bot details
        const botData = await botApi.getBot(botId);
        setBot(botData);
        
        // Fetch widget configuration
        const widgetConfig = await widgetApi.getWidgetConfig(botId);
        setConfig(widgetConfig);
      } catch (error) {
        console.error('Error fetching widget configuration:', error);
        setSnackbar({
          open: true,
          message: 'Failed to load widget configuration',
          severity: 'error',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [botId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSwitchChange = (e) => {
    const { name, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: checked,
    }));
  };

  const handleColorChange = (color) => {
    setConfig((prev) => ({
      ...prev,
      primary_color: color.hex,
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      await widgetApi.updateWidgetConfig(botId, config);
      
      setSnackbar({
        open: true,
        message: 'Widget configuration saved successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error saving widget configuration:', error);
      setSnackbar({
        open: true,
        message: 'Failed to save widget configuration',
        severity: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleCopyCode = () => {
    const embedCode = getEmbedCode();
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  const getEmbedCode = () => {
    return `<script>
  (function(w, d, s, o) {
    w.AIChatWidget = o;
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(o)) return;
    js = d.createElement(s); js.id = o;
    js.src = '${window.location.origin}/widget/ai-chatbot-widget.js';
    js.async = 1;
    js.dataset.botId = '${botId}';
    fjs.parentNode.insertBefore(js, fjs);
  }(window, document, 'script', 'ai-chatbot-widget'));
</script>`;
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({
      ...prev,
      open: false,
    }));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!bot) {
    return (
      <Box>
        <Typography variant="h5" color="error">
          Bot not found
        </Typography>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/bots')}
          sx={{ mt: 2 }}
        >
          Back to Bots
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton
          onClick={() => navigate(`/bots/${botId}`)}
          sx={{ mr: 1 }}
        >
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          Widget Configuration: {bot.name}
        </Typography>
      </Box>

      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="Appearance" />
          <Tab label="Behavior" />
          <Tab label="Embed Code" />
        </Tabs>

        {/* Appearance Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Theme & Colors
              </Typography>
              
              <FormControl component="fieldset" sx={{ mb: 3 }}>
                <FormLabel component="legend">Theme</FormLabel>
                <RadioGroup
                  row
                  name="theme"
                  value={config.theme}
                  onChange={handleInputChange}
                >
                  <FormControlLabel value="light" control={<Radio />} label="Light" />
                  <FormControlLabel value="dark" control={<Radio />} label="Dark" />
                </RadioGroup>
              </FormControl>
              
              <Box sx={{ mb: 3 }}>
                <FormLabel component="legend" sx={{ mb: 1 }}>
                  Primary Color
                </FormLabel>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 1,
                      bgcolor: config.primary_color,
                      mr: 2,
                      cursor: 'pointer',
                      border: '1px solid #ddd',
                    }}
                    onClick={() => setColorPickerOpen(!colorPickerOpen)}
                  />
                  <TextField
                    size="small"
                    value={config.primary_color}
                    name="primary_color"
                    onChange={handleInputChange}
                    sx={{ width: 120 }}
                  />
                </Box>
                {colorPickerOpen && (
                  <Box sx={{ position: 'absolute', zIndex: 2, mt: 1 }}>
                    <Box
                      sx={{
                        position: 'fixed',
                        top: 0,
                        right: 0,
                        bottom: 0,
                        left: 0,
                      }}
                      onClick={() => setColorPickerOpen(false)}
                    />
                    <ChromePicker
                      color={config.primary_color}
                      onChange={handleColorChange}
                    />
                  </Box>
                )}
              </Box>
              
              <FormControl component="fieldset" sx={{ mb: 3 }}>
                <FormLabel component="legend">Position</FormLabel>
                <RadioGroup
                  name="position"
                  value={config.position}
                  onChange={handleInputChange}
                >
                  <FormControlLabel value="bottom-right" control={<Radio />} label="Bottom Right" />
                  <FormControlLabel value="bottom-left" control={<Radio />} label="Bottom Left" />
                </RadioGroup>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Preview
              </Typography>
              <Card
                sx={{
                  bgcolor: config.theme === 'dark' ? '#1e1e1e' : '#ffffff',
                  color: config.theme === 'dark' ? '#ffffff' : '#000000',
                  borderRadius: 2,
                  overflow: 'hidden',
                  boxShadow: 3,
                }}
              >
                <Box
                  sx={{
                    bgcolor: config.primary_color,
                    color: '#ffffff',
                    p: 2,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  <Box
                    sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      mr: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {bot.name.charAt(0).toUpperCase()}
                  </Box>
                  <Typography variant="subtitle1">
                    {bot.name}
                  </Typography>
                </Box>
                
                <Box sx={{ p: 2, height: 200, overflowY: 'auto' }}>
                  <Box
                    sx={{
                      bgcolor: config.theme === 'dark' ? '#2e2e2e' : '#f5f5f5',
                      color: config.theme === 'dark' ? '#ffffff' : '#000000',
                      p: 1.5,
                      borderRadius: 2,
                      maxWidth: '80%',
                      mb: 2,
                    }}
                  >
                    <Typography variant="body2">
                      {config.welcome_message || `Hi there! I'm ${bot.name}. How can I help you today?`}
                    </Typography>
                  </Box>
                </Box>
                
                <Box
                  sx={{
                    p: 2,
                    borderTop: '1px solid',
                    borderColor: config.theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                    display: 'flex',
                  }}
                >
                  <TextField
                    fullWidth
                    size="small"
                    placeholder={config.placeholder_text}
                    variant="outlined"
                    sx={{
                      mr: 1,
                      '& .MuiOutlinedInput-root': {
                        bgcolor: config.theme === 'dark' ? '#2e2e2e' : '#ffffff',
                        color: config.theme === 'dark' ? '#ffffff' : '#000000',
                      },
                    }}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    sx={{ bgcolor: config.primary_color }}
                  >
                    Send
                  </Button>
                </Box>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Behavior Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Messages
              </Typography>
              
              <TextField
                fullWidth
                label="Welcome Message"
                name="welcome_message"
                value={config.welcome_message}
                onChange={handleInputChange}
                multiline
                rows={3}
                placeholder={`Hi there! I'm ${bot.name}. How can I help you today?`}
                sx={{ mb: 3 }}
              />
              
              <TextField
                fullWidth
                label="Input Placeholder"
                name="placeholder_text"
                value={config.placeholder_text}
                onChange={handleInputChange}
                sx={{ mb: 3 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={config.show_sources}
                    onChange={handleSwitchChange}
                    name="show_sources"
                  />
                }
                label="Show sources in responses"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Additional Settings
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                These settings control how the widget behaves on your website.
              </Typography>
              
              <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Auto-Open Delay
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Set to 0 to disable auto-open. Coming soon.
                  </Typography>
                </CardContent>
              </Card>
              
              <Card sx={{ mb: 2, bgcolor: '#f5f5f5' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    Page URL Targeting
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Show widget only on specific pages. Coming soon.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Embed Code Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Website Integration
          </Typography>
          
          <Typography variant="body2" paragraph>
            Copy and paste this code into your website's HTML, just before the closing &lt;/body&gt; tag.
          </Typography>
          
          <Paper
            sx={{
              p: 2,
              bgcolor: '#f5f5f5',
              borderRadius: 1,
              fontFamily: 'monospace',
              position: 'relative',
              mb: 3,
            }}
          >
            <Box sx={{ overflow: 'auto', maxHeight: 200 }}>
              <pre style={{ margin: 0 }}>{getEmbedCode()}</pre>
            </Box>
            <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
              <IconButton
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  bgcolor: copied ? 'success.main' : 'background.paper',
                  color: copied ? 'white' : 'inherit',
                  '&:hover': {
                    bgcolor: copied ? 'success.dark' : 'action.hover',
                  },
                }}
                onClick={handleCopyCode}
              >
                {copied ? <CheckIcon /> : <CopyIcon />}
              </IconButton>
            </Tooltip>
          </Paper>
          
          <Typography variant="h6" gutterBottom>
            Testing
          </Typography>
          
          <Typography variant="body2" paragraph>
            You can test your widget using the preview URL below:
          </Typography>
          
          <TextField
            fullWidth
            variant="outlined"
            value={`${window.location.origin}/widget-preview/${botId}`}
            InputProps={{
              readOnly: true,
            }}
            sx={{ mb: 2 }}
          />
          
          <Button
            variant="outlined"
            component="a"
            href={`${window.location.origin}/widget-preview/${botId}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open Preview
          </Button>
        </TabPanel>
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <CircularProgress size={24} /> : 'Save Configuration'}
        </Button>
      </Box>

      {/* Snackbar for notifications */}
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