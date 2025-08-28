import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  CardMedia,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  CircularProgress,
  Snackbar,
  Alert,
  Chip,
  Divider,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { botApi } from '../services/api';
import { useAuth } from '../contexts/AuthContext'; // Fixed import path

export default function Bots() {
  const navigate = useNavigate();
  const { user } = useAuth(); // Get user from auth context
  
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    website_url: '',
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  useEffect(() => {
    // Debug: Check if user is authenticated
    console.log('Bots component - User:', user);
    console.log('Bots component - User ID:', user?.id);
    
    if (user) {
      fetchBots();
    } else {
      console.warn('No user found in auth context');
      setLoading(false);
    }
  }, [user]);

  const fetchBots = async () => {
    try {
      setLoading(true);
      
      // Debug: Check authentication
      const token = localStorage.getItem('auth_token');
      console.log('Fetching bots with token:', token ? token.substring(0, 20) + '...' : 'No token');
      
      const data = await botApi.getBots();
      console.log('Bots data received:', data);
      setBots(data);
    } catch (error) {
      console.error('Error fetching bots:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      setSnackbar({
        open: true,
        message: 'Failed to load bots',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (bot = null) => {
    if (bot) {
      setSelectedBot(bot);
      setFormData({
        name: bot.name,
        description: bot.description || '',
        website_url: bot.website_url || '',
      });
    } else {
      setSelectedBot(null);
      setFormData({
        name: '',
        description: '',
        website_url: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedBot(null);
  };

  const handleOpenDeleteDialog = (bot) => {
    setSelectedBot(bot);
    setDeleteDialog(true);
  };

  const handleCloseDeleteDialog = () => {
    setDeleteDialog(false);
    setSelectedBot(null);
  };

  const handleTestAuth = async () => {
    try {
      const result = await botApi.testAuth();
      console.log('Auth test result:', result);
      setSnackbar({
        open: true,
        message: `Auth test successful: ${result.user_email}`,
        severity: 'success',
      });
    } catch (error) {
      console.error('Auth test failed:', error);
      setSnackbar({
        open: true,
        message: 'Auth test failed',
        severity: 'error',
      });
    }
  };

  const handleDebugBots = async () => {
    try {
      const result = await botApi.debugAllBots();
      console.log('Debug result:', result);
      setSnackbar({
        open: true,
        message: `Debug: ${result.total_bots_in_db} total bots, ${result.user_bots_count} user bots`,
        severity: 'info',
      });
    } catch (error) {
      console.error('Debug failed:', error);
      setSnackbar({
        open: true,
        message: 'Debug failed',
        severity: 'error',
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async () => {
    try {
      if (selectedBot) {
        // Update existing bot
        await botApi.updateBot(selectedBot.id, formData);
        setSnackbar({
          open: true,
          message: 'Bot updated successfully',
          severity: 'success',
        });
      } else {
        // Create new bot
        await botApi.createBot(formData);
        setSnackbar({
          open: true,
          message: 'Bot created successfully',
          severity: 'success',
        });
      }
      
      handleCloseDialog();
      fetchBots();
    } catch (error) {
      console.error('Error saving bot:', error);
      setSnackbar({
        open: true,
        message: `Failed to ${selectedBot ? 'update' : 'create'} bot`,
        severity: 'error',
      });
    }
  };

  const handleDelete = async () => {
    try {
      await botApi.deleteBot(selectedBot.id);
      setSnackbar({
        open: true,
        message: 'Bot deleted successfully',
        severity: 'success',
      });
      handleCloseDeleteDialog();
      fetchBots();
    } catch (error) {
      console.error('Error deleting bot:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete bot',
        severity: 'error',
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({
      ...prev,
      open: false,
    }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          My Bots
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={handleTestAuth}
            size="small"
          >
            Test Auth
          </Button>
          <Button
            variant="outlined"
            onClick={handleDebugBots}
            size="small"
          >
            Debug Bots
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Bot
          </Button>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {bots.length > 0 ? (
            bots.map((bot) => (
              <Grid item xs={12} sm={6} md={4} key={bot.id}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                  <CardMedia
                    component="div"
                    sx={{
                      height: 140,
                      background: (theme) => `linear-gradient(135deg, ${theme.palette.primary.main} 0%, #8b5cf6 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography variant="h4" color="white">
                      {bot.name.charAt(0).toUpperCase()}
                    </Typography>
                  </CardMedia>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div" gutterBottom sx={{ fontWeight: 700 }}>
                      {bot.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {bot.description || 'No description'}
                    </Typography>
                    {bot.website_url && (
                      <Typography variant="body2" color="text.secondary">
                        Website: {bot.website_url}
                      </Typography>
                    )}
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Chip 
                        label={`${bot.messages_count || 0} messages`} 
                        size="small" 
                        color="primary" 
                        variant="outlined" 
                      />
                      <Chip 
                        label={`${bot.documents_count || 0} docs`} 
                        size="small" 
                        color="secondary" 
                        variant="outlined" 
                      />
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => navigate(`/bots/${bot.id}`)} variant="text">
                      Manage
                    </Button>
                    <Button size="small" onClick={() => navigate(`/bots/${bot.id}/widget`)} variant="text">
                      Widget
                    </Button>
                    <Box sx={{ flexGrow: 1 }} />
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(bot)}
                      aria-label="edit"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDeleteDialog(bot)}
                      aria-label="delete"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Box
                sx={{
                  p: 4,
                  textAlign: 'center',
                  border: '1px dashed',
                  borderColor: 'divider',
                  borderRadius: 2,
                }}
              >
                <Typography variant="h6" gutterBottom>
                  No Bots Found
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create your first bot to get started
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => handleOpenDialog()}
                >
                  Create Bot
                </Button>
              </Box>
            </Grid>
          )}
        </Grid>
      )}

      {/* Create/Edit Bot Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{selectedBot ? 'Edit Bot' : 'Create Bot'}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Bot Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleInputChange}
            required
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="description"
            label="Description"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.description}
            onChange={handleInputChange}
            multiline
            rows={3}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="website_url"
            label="Website URL"
            type="url"
            fullWidth
            variant="outlined"
            value={formData.website_url}
            onChange={handleInputChange}
            placeholder="https://example.com"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained" disabled={!formData.name}>
            {selectedBot ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialog} onClose={handleCloseDeleteDialog}>
        <DialogTitle>Delete Bot</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedBot?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

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