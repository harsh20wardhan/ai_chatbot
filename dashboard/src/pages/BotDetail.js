import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Paper,
  Divider,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondary,
  LinearProgress,
  TextField,
  InputAdornment,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  Web as WebIcon,
  Description as DocumentIcon,
  Chat as ChatIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
} from '@mui/icons-material';
import { botApi, crawlApi, documentApi, chatApi } from '../services/api';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`bot-tabpanel-${index}`}
      aria-labelledby={`bot-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function BotDetail() {
  const { botId } = useParams();
  const navigate = useNavigate();
  
  const [tabValue, setTabValue] = useState(0);
  const [bot, setBot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crawlJobs, setCrawlJobs] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [crawlUrl, setCrawlUrl] = useState('');
  const [openCrawlDialog, setOpenCrawlDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [activeCrawlJob, setActiveCrawlJob] = useState(null);
  const [crawlStarting, setCrawlStarting] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success',
  });
  const [refreshing, setRefreshing] = useState({
    crawlJobs: false,
    documents: false,
    conversations: false,
  });

  useEffect(() => {
    fetchBotDetails();
  }, [botId]);

  // Set up automatic refresh when there's an active crawl job
  useEffect(() => {
    let intervalId;
    
    if (activeCrawlJob) {
      // Refresh every 3 seconds when there's an active crawl job
      intervalId = setInterval(() => {
        fetchCrawlJobs();
      }, 3000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [activeCrawlJob]);

  const fetchBotDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch bot details
      const botData = await botApi.getBot(botId);
      setBot(botData);
      
      // Fetch crawl jobs
      await fetchCrawlJobs();
      
      // Fetch documents
      await fetchDocuments();
      
      // Fetch conversations
      await fetchConversations();
    } catch (error) {
      console.error('Error fetching bot details:', error);
      setSnackbar({
        open: true,
        message: 'Failed to load bot details',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCrawlJobs = async () => {
    try {
      setRefreshing(prev => ({ ...prev, crawlJobs: true }));
      
      // Fetch both regular and realtime crawl jobs for this specific bot
      const [regularJobs, realtimeJobs] = await Promise.allSettled([
        crawlApi.getCrawlJobsByBot(botId),
        crawlApi.getRealtimeCrawlJobsByBot(botId)
      ]);
      
      const allJobs = [];
      
      // Add regular crawl jobs if successful
      if (regularJobs.status === 'fulfilled') {
        allJobs.push(...regularJobs.value.map(job => ({ ...job, type: 'regular' })));
      }
      
      // Add realtime crawl jobs if successful
      if (realtimeJobs.status === 'fulfilled') {
        allJobs.push(...realtimeJobs.value.map(job => ({ ...job, type: 'realtime' })));
      }
      
      // Sort by creation date (newest first)
      allJobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      // Check for active crawl job
      const activeJob = allJobs.find(job => 
        job.status === 'pending' || job.status === 'running' || job.status === 'processing'
      );
      
      // Check if previously active job completed
      if (activeCrawlJob && !activeJob) {
        const completedJob = allJobs.find(job => job.id === activeCrawlJob.id);
        if (completedJob && (completedJob.status === 'completed' || completedJob.status === 'failed')) {
          setSnackbar({
            open: true,
            message: completedJob.status === 'completed' 
              ? `Crawl completed successfully! ${completedJob.pages_crawled || 0} pages crawled.`
              : `Crawl failed: ${completedJob.error || 'Unknown error'}`,
            severity: completedJob.status === 'completed' ? 'success' : 'error',
          });
        }
      }
      
      setActiveCrawlJob(activeJob || null);
      setCrawlJobs(allJobs);
    } catch (error) {
      console.error('Error fetching crawl jobs:', error);
      // If the API call fails, show empty array instead of mock data
      setCrawlJobs([]);
      setActiveCrawlJob(null);
    } finally {
      setRefreshing(prev => ({ ...prev, crawlJobs: false }));
    }
  };

  const fetchDocuments = async () => {
    try {
      setRefreshing(prev => ({ ...prev, documents: true }));
      
      const docs = await documentApi.getDocuments(botId);
      setDocuments(docs);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setRefreshing(prev => ({ ...prev, documents: false }));
    }
  };

  const fetchConversations = async () => {
    try {
      setRefreshing(prev => ({ ...prev, conversations: true }));
      
      const convos = await chatApi.getConversations(botId);
      setConversations(convos);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setRefreshing(prev => ({ ...prev, conversations: false }));
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleCrawlUrlChange = (e) => {
    setCrawlUrl(e.target.value);
  };

  const handleOpenCrawlDialog = () => {
    setOpenCrawlDialog(true);
  };

  const handleCloseCrawlDialog = () => {
    setOpenCrawlDialog(false);
  };

  const handleStartCrawl = async () => {
    if (!crawlUrl || crawlStarting || activeCrawlJob) return;
    
    try {
      setCrawlStarting(true);
      
      // Use realtime crawl for better user experience
      const result = await crawlApi.startRealtimeCrawl(botId, crawlUrl);
      
      setSnackbar({
        open: true,
        message: 'Realtime crawl started successfully',
        severity: 'success',
      });
      
      handleCloseCrawlDialog();
      setCrawlUrl('');
      
      // Refresh the crawl jobs list immediately to get the new job
      await fetchCrawlJobs();
      
    } catch (error) {
      console.error('Error starting crawl job:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.error || 'Failed to start crawl job',
        severity: 'error',
      });
    } finally {
      setCrawlStarting(false);
    }
  };

  const handleOpenDeleteDialog = () => {
    setOpenDeleteDialog(true);
  };

  const handleCloseDeleteDialog = () => {
    setOpenDeleteDialog(false);
  };

  const handleDeleteBot = async () => {
    try {
      await botApi.deleteBot(botId);
      
      setSnackbar({
        open: true,
        message: 'Bot deleted successfully',
        severity: 'success',
      });
      
      navigate('/bots');
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
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'completed':
        return <Chip icon={<CheckCircleIcon />} label="Completed" color="success" size="small" />;
      case 'pending':
        return <Chip icon={<PendingIcon />} label="Pending" color="primary" size="small" />;
      case 'failed':
        return <Chip icon={<ErrorIcon />} label="Failed" color="error" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4 }}>
        <LinearProgress sx={{ width: '100%', mb: 2 }} />
        <Typography>Loading bot details...</Typography>
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
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <IconButton
            onClick={() => navigate('/bots')}
            sx={{ mr: 1 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1">
            {bot.name}
          </Typography>
        </Box>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {bot.description || 'No description'}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => navigate(`/bots/${botId}/widget`)}
          >
            Widget Settings
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleOpenDeleteDialog}
          >
            Delete Bot
          </Button>
        </Box>
      </Box>
      
      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab icon={<WebIcon />} label="Crawled Websites" />
          <Tab icon={<DocumentIcon />} label="Documents" />
          <Tab icon={<ChatIcon />} label="Conversations" />
        </Tabs>
        
        {/* Crawled Websites Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Crawled Websites</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchCrawlJobs}
                disabled={refreshing.crawlJobs}
                sx={{ mr: 1 }}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={activeCrawlJob ? <PendingIcon /> : <AddIcon />}
                onClick={handleOpenCrawlDialog}
                disabled={activeCrawlJob || crawlStarting}
                color={activeCrawlJob ? "warning" : "primary"}
              >
                {activeCrawlJob ? "Crawling in Progress..." : "Crawl Website"}
              </Button>
            </Box>
          </Box>
          
          {crawlJobs.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 2 }}>
                No websites have been crawled yet.
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenCrawlDialog}
              >
                Crawl Your First Website
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={2}>
              {crawlJobs.map((job) => (
                <Grid item xs={12} key={job.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {job.url}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Status: {getStatusChip(job.status)} {job.type && (
                            <Chip size="small" label={job.type} variant="outlined" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Pages: {job.pages_crawled || 0}
                        </Typography>
                      </Box>
                      
                      {/* Show progress bar for active crawl jobs */}
                      {(job.status === 'pending' || job.status === 'running' || job.status === 'processing') && (
                        <Box sx={{ mb: 2 }}>
                          <LinearProgress />
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                            Crawling in progress...
                          </Typography>
                        </Box>
                      )}
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">
                          Started: {formatDate(job.created_at)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Completed: {formatDate(job.completed_at)}
                        </Typography>
                      </Box>
                      
                      {job.error && (
                        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                          Error: {job.error}
                        </Typography>
                      )}
                    </CardContent>
                    <CardActions>
                      <Button size="small">View Pages</Button>
                      <Button size="small" color="error">Delete</Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>
        
        {/* Documents Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Documents</Typography>
            <Box>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchDocuments}
                disabled={refreshing.documents}
                sx={{ mr: 1 }}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                component="label"
              >
                Upload Document
                <input
                  type="file"
                  hidden
                  accept=".pdf,.docx,.txt,.xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      documentApi.uploadDocument(botId, e.target.files[0])
                        .then(() => {
                          setSnackbar({
                            open: true,
                            message: 'Document uploaded successfully',
                            severity: 'success',
                          });
                          fetchDocuments();
                        })
                        .catch((error) => {
                          console.error('Error uploading document:', error);
                          setSnackbar({
                            open: true,
                            message: 'Failed to upload document',
                            severity: 'error',
                          });
                        });
                    }
                  }}
                />
              </Button>
            </Box>
          </Box>
          
          {documents.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 2 }}>
                No documents have been uploaded yet.
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                component="label"
              >
                Upload Your First Document
                <input
                  type="file"
                  hidden
                  accept=".pdf,.docx,.txt,.xlsx,.xls"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      documentApi.uploadDocument(botId, e.target.files[0])
                        .then(() => {
                          setSnackbar({
                            open: true,
                            message: 'Document uploaded successfully',
                            severity: 'success',
                          });
                          fetchDocuments();
                        })
                        .catch((error) => {
                          console.error('Error uploading document:', error);
                          setSnackbar({
                            open: true,
                            message: 'Failed to upload document',
                            severity: 'error',
                          });
                        });
                    }
                  }}
                />
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={2}>
              {documents.map((doc) => (
                <Grid item xs={12} sm={6} md={4} key={doc.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom noWrap>
                        {doc.file_name}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Chip
                          label={doc.file_type.toUpperCase()}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                        <Typography variant="body2" color="text.secondary">
                          {getStatusChip(doc.status)}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary">
                        Uploaded: {formatDate(doc.created_at)}
                      </Typography>
                      
                      {doc.error && (
                        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                          Error: {doc.error}
                        </Typography>
                      )}
                    </CardContent>
                    <CardActions>
                      <Button size="small">View</Button>
                      <Button size="small" color="error">Delete</Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </TabPanel>
        
        {/* Conversations Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Conversations</Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchConversations}
              disabled={refreshing.conversations}
            >
              Refresh
            </Button>
          </Box>
          
          {conversations.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1">
                No conversations yet.
              </Typography>
            </Paper>
          ) : (
            <List>
              {conversations.map((conversation) => (
                <React.Fragment key={conversation.id}>
                  <ListItem
                    button
                    component={RouterLink}
                    to={`/conversations/${conversation.id}`}
                  >
                    <ListItemIcon>
                      <ChatIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={conversation.title || `Conversation ${conversation.id.slice(0, 8)}`}
                      secondary={`${conversation.messages_count} messages • ${formatDate(conversation.created_at)}`}
                    />
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          )}
        </TabPanel>
      </Paper>
      
      {/* Crawl Dialog */}
      <Dialog open={openCrawlDialog} onClose={handleCloseCrawlDialog}>
        <DialogTitle>Crawl Website</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the URL of the website you want to crawl. The crawler will extract content from the website and use it to train your bot.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Website URL"
            type="url"
            fullWidth
            variant="outlined"
            value={crawlUrl}
            onChange={handleCrawlUrlChange}
            placeholder="https://example.com"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <WebIcon />
                </InputAdornment>
              ),
            }}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCrawlDialog}>Cancel</Button>
          <Button
            onClick={handleStartCrawl}
            variant="contained"
            disabled={!crawlUrl || crawlStarting || activeCrawlJob}
          >
            {crawlStarting ? "Starting..." : "Start Crawl"}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Dialog */}
      <Dialog open={openDeleteDialog} onClose={handleCloseDeleteDialog}>
        <DialogTitle>Delete Bot</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{bot.name}"? This action cannot be undone and will remove all associated data, including crawled websites, documents, and conversations.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>Cancel</Button>
          <Button onClick={handleDeleteBot} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
      
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