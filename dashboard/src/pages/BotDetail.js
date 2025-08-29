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
  CircularProgress,
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
  
  // Enhanced crawling parameters
  const [crawlOptions, setCrawlOptions] = useState({
    max_pages: 100,
    max_depth: 5,
    exclude_patterns: '',
    include_patterns: '',
    respect_robots_txt: true,
    delay_between_requests: 1.0
  });
  
  // View pages functionality
  const [viewingPages, setViewingPages] = useState(false);
  const [selectedCrawlJob, setSelectedCrawlJob] = useState(null);
  const [crawledPages, setCrawledPages] = useState([]);
  const [pagesLoading, setPagesLoading] = useState(false);
  
  // Document viewing functionality
  const [viewingDocument, setViewingDocument] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documentContent, setDocumentContent] = useState('');
  const [documentLoading, setDocumentLoading] = useState(false);
  
  // Document deletion confirmation
  const [openDeleteDocumentDialog, setOpenDeleteDocumentDialog] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState(null);
  
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

  const handleCrawlOptionChange = (field, value) => {
    setCrawlOptions(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleOpenCrawlDialog = () => {
    // Load default crawling settings from localStorage
    const savedCrawlingSettings = localStorage.getItem('defaultCrawlingSettings');
    if (savedCrawlingSettings) {
      try {
        const defaults = JSON.parse(savedCrawlingSettings);
        setCrawlOptions({
          max_pages: defaults.default_max_pages || 100,
          max_depth: defaults.default_max_depth || 5,
          exclude_patterns: defaults.default_exclude_patterns || '',
          include_patterns: defaults.default_include_patterns || '',
          respect_robots_txt: defaults.default_respect_robots_txt !== undefined ? defaults.default_respect_robots_txt : true,
          delay_between_requests: defaults.default_delay_between_requests || 1.0
        });
      } catch (error) {
        console.error('Failed to parse saved crawling settings:', error);
        // Use default values if parsing fails
        setCrawlOptions({
          max_pages: 100,
          max_depth: 5,
          exclude_patterns: '',
          include_patterns: '',
          respect_robots_txt: true,
          delay_between_requests: 1.0
        });
      }
    }
    
    setOpenCrawlDialog(true);
  };

  const handleCloseCrawlDialog = () => {
    setOpenCrawlDialog(false);
    // Reset options to defaults
    setCrawlOptions({
      max_pages: 100,
      max_depth: 5,
      exclude_patterns: '',
      include_patterns: '',
      respect_robots_txt: true,
      delay_between_requests: 1.0
    });
  };

  const handleStartCrawl = async () => {
    if (!crawlUrl || crawlStarting || activeCrawlJob) return;
    
    try {
      setCrawlStarting(true);
      
      // Parse patterns from comma-separated strings
      const excludePatterns = crawlOptions.exclude_patterns
        .split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0);
      
      const includePatterns = crawlOptions.include_patterns
        .split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0);
      
      // Use enhanced realtime crawl for better user experience
      const result = await crawlApi.startEnhancedRealtimeCrawl(botId, crawlUrl, {
        ...crawlOptions,
        exclude_patterns: excludePatterns,
        include_patterns: includePatterns
      });
      
      setSnackbar({
        open: true,
        severity: 'success',
        message: 'Enhanced realtime crawl started successfully',
      });
      
      handleCloseCrawlDialog();
      setCrawlUrl('');
      
      // Refresh the crawl jobs list immediately to get the new job
      await fetchCrawlJobs();
      
    } catch (error) {
      console.error('Error starting enhanced crawl job:', error);
      setSnackbar({
        open: true,
        severity: 'error',
        message: error.response?.data?.error || 'Failed to start enhanced crawl job',
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

  const handleViewPages = async (job) => {
    try {
      setSelectedCrawlJob(job);
      setPagesLoading(true);
      setViewingPages(true);
      
      // Fetch real crawled pages from the API
      const pages = await crawlApi.getCrawledPages(job.id);
      setCrawledPages(pages);
    } catch (error) {
      console.error('Error fetching crawled pages:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to fetch crawled pages',
        severity: 'error',
      });
      // Set empty array if API call fails
      setCrawledPages([]);
    } finally {
      setPagesLoading(false);
    }
  };

  const handleClosePagesDialog = () => {
    setViewingPages(false);
    setSelectedCrawlJob(null);
    setCrawledPages([]);
  };

  const handleDeleteCrawlJob = async (jobId) => {
    try {
      // This would be a real API call in production
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Remove the job from the local state
      setCrawlJobs(prev => prev.filter(job => job.id !== jobId));
      
      setSnackbar({
        open: true,
        message: 'Crawl job deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      console.error('Error deleting crawl job:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete crawl job',
        severity: 'error',
      });
    }
  };

  const handleViewDocument = async (doc) => {
    try {
      setSelectedDocument(doc);
      setDocumentLoading(true);
      setViewingDocument(true);
      
      // Fetch document content from the API
      const response = await documentApi.getDocument(doc.id);
      setDocumentContent(response.content || 'Document content not available');
    } catch (error) {
      console.error('Error fetching document content:', error);
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to fetch document content',
        severity: 'error',
      });
      setDocumentContent('Failed to load document content');
    } finally {
      setDocumentLoading(false);
    }
  };

  const handleCloseDocumentDialog = () => {
    setViewingDocument(false);
    setSelectedDocument(null);
    setDocumentContent('');
  };

  const handleDeleteDocument = async (documentId) => {
    try {
      await documentApi.deleteDocument(documentId);
      
      setSnackbar({
        open: true,
        message: 'Document deleted successfully',
        severity: 'success',
      });
      
      // Refresh documents list
      fetchDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      setSnackbar({
        open: true,
        message: 'Failed to delete document',
        severity: 'error',
      });
    }
  };

  const handleOpenDeleteDocumentDialog = (doc) => {
    setDocumentToDelete(doc);
    setOpenDeleteDocumentDialog(true);
  };

  const handleCloseDeleteDocumentDialog = () => {
    setOpenDeleteDocumentDialog(false);
    setDocumentToDelete(null);
  };

  const handleConfirmDeleteDocument = async () => {
    if (documentToDelete) {
      await handleDeleteDocument(documentToDelete.id);
      handleCloseDeleteDocumentDialog();
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
          <Typography variant="h3" component="h1" sx={{ fontWeight: 800 }}>
            {bot.name}
          </Typography>
        </Box>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {bot.description || 'No description'}
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
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
                {activeCrawlJob ? "Crawling in Progress..." : "Enhanced Crawl Website"}
              </Button>
            </Box>
          </Box>
          
          {/* Enhanced Crawling Statistics */}
          {crawlJobs.length > 0 && (
            <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.50' }}>
              <Typography variant="subtitle2" color="primary.700" sx={{ mb: 1, fontWeight: 'bold' }}>
                Enhanced Crawling Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="primary.main">
                      {crawlJobs.length}
                    </Typography>
                    <Typography variant="caption" color="primary.700">
                      Total Crawl Jobs
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="success.main">
                      {crawlJobs.filter(job => job.status === 'completed').length}
                    </Typography>
                    <Typography variant="caption" color="primary.700">
                      Completed
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="warning.main">
                      {crawlJobs.filter(job => job.status === 'running' || job.status === 'pending').length}
                    </Typography>
                    <Typography variant="caption" color="primary.700">
                      In Progress
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" color="error.main">
                      {crawlJobs.filter(job => job.status === 'failed').length}
                    </Typography>
                    <Typography variant="caption" color="primary.700">
                      Failed
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              {/* Advanced Statistics */}
              <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'primary.200' }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="primary.700">
                      <strong>Total Pages Crawled:</strong> {crawlJobs.reduce((sum, job) => sum + (job.pages_crawled || 0), 0)}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <Typography variant="caption" color="primary.700">
                      <strong>Average Depth:</strong> {Math.round(crawlJobs.reduce((sum, job) => sum + (job.max_depth || 0), 0) / crawlJobs.length || 0)}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            </Paper>
          )}
          
          {crawlJobs.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                No websites have been crawled yet.
              </Typography>
              <Button
                variant="outlined"
                onClick={handleOpenCrawlDialog}
                startIcon={<AddIcon />}
              >
                Start Enhanced Crawling
              </Button>
            </Box>
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
                      
                      {/* Enhanced Crawling Parameters */}
                      <Box sx={{ mb: 2, p: 1.5, bgcolor: 'grey.50', borderRadius: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
                          Crawling Configuration:
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Max Pages: {job.max_pages || 'N/A'}
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Max Depth: {job.max_depth || 'N/A'}
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Delay: {job.delay_between_requests || 'N/A'}s
                            </Typography>
                          </Grid>
                          <Grid item xs={6} sm={3}>
                            <Typography variant="caption" color="text.secondary">
                              Robots.txt: {job.respect_robots_txt ? 'Yes' : 'No'}
                            </Typography>
                          </Grid>
                        </Grid>
                        
                        {/* Pattern Filters */}
                        {(job.exclude_patterns && job.exclude_patterns.length > 0) && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Excluded: {job.exclude_patterns.join(', ')}
                            </Typography>
                          </Box>
                        )}
                        
                        {(job.include_patterns && job.include_patterns.length > 0) && (
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Included: {job.include_patterns.join(', ')}
                            </Typography>
                          </Box>
                        )}
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
                      <Button size="small" onClick={() => handleViewPages(job)}>View Pages</Button>
                      <Button size="small" color="error" onClick={() => handleDeleteCrawlJob(job.id)}>Delete</Button>
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
                        {doc.filename || doc.file_name || 'Untitled Document'}
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
                      <Button size="small" onClick={() => handleViewDocument(doc)}>View</Button>
                      <Button size="small" color="error" onClick={() => handleOpenDeleteDocumentDialog(doc)}>Delete</Button>
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
      
      {/* Enhanced Crawl Dialog */}
      <Dialog open={openCrawlDialog} onClose={handleCloseCrawlDialog} maxWidth="md" fullWidth>
        <DialogTitle>Enhanced Website Crawling</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 3 }}>
            Configure advanced crawling options to extract comprehensive content from websites. 
            The enhanced crawler will go deeper and extract more content for better AI training.
          </DialogContentText>
          
          {/* URL Input */}
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
            sx={{ mb: 3 }}
          />
          
          {/* Crawling Options Grid */}
          <Grid container spacing={3}>
            {/* Max Pages and Depth */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maximum Pages"
                type="number"
                value={crawlOptions.max_pages}
                onChange={(e) => handleCrawlOptionChange('max_pages', parseInt(e.target.value) || 100)}
                inputProps={{ min: 1, max: 1000 }}
                helperText="Maximum number of pages to crawl (1-1000)"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maximum Depth"
                type="number"
                value={crawlOptions.max_depth}
                onChange={(e) => handleCrawlOptionChange('max_depth', parseInt(e.target.value) || 5)}
                inputProps={{ min: 1, max: 10 }}
                helperText="How deep to follow links (1-10 levels)"
                variant="outlined"
              />
            </Grid>
            
            {/* Pattern Filters */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Exclude Patterns"
                placeholder="/admin, /api, /private"
                value={crawlOptions.exclude_patterns}
                onChange={(e) => handleCrawlOptionChange('exclude_patterns', e.target.value)}
                helperText="Comma-separated URL patterns to exclude"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Include Patterns"
                placeholder="/blog, /docs, /articles"
                value={crawlOptions.include_patterns}
                onChange={(e) => handleCrawlOptionChange('include_patterns', e.target.value)}
                helperText="Comma-separated URL patterns to include (optional)"
                variant="outlined"
              />
            </Grid>
            
            {/* Advanced Options */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Delay Between Requests (seconds)"
                type="number"
                value={crawlOptions.delay_between_requests}
                onChange={(e) => handleCrawlOptionChange('delay_between_requests', parseFloat(e.target.value) || 1.0)}
                inputProps={{ min: 0.1, max: 10, step: 0.1 }}
                helperText="Be respectful to servers (0.1-10 seconds)"
                variant="outlined"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', height: '100%', pt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                  Respect robots.txt:
                </Typography>
                <Button
                  variant={crawlOptions.respect_robots_txt ? "contained" : "outlined"}
                  size="small"
                  onClick={() => handleCrawlOptionChange('respect_robots_txt', !crawlOptions.respect_robots_txt)}
                  color={crawlOptions.respect_robots_txt ? "success" : "primary"}
                >
                  {crawlOptions.respect_robots_txt ? "Yes" : "No"}
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
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseCrawlDialog}>Cancel</Button>
          <Button
            onClick={handleStartCrawl}
            variant="contained"
            disabled={!crawlUrl || crawlStarting || activeCrawlJob}
            startIcon={<WebIcon />}
          >
            {crawlStarting ? "Starting Enhanced Crawl..." : "Start Enhanced Crawl"}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* View Crawled Pages Dialog */}
      <Dialog open={viewingPages} onClose={handleClosePagesDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          Crawled Pages - {selectedCrawlJob?.url}
        </DialogTitle>
        <DialogContent>
          {pagesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : crawledPages.length === 0 ? (
            <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No pages found for this crawl job.
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {crawledPages.map((page) => (
                <Grid item xs={12} key={page.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {page.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {page.url}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                          Content Length: {page.content_length} characters
                        </Typography>
                        <Chip 
                          label={page.status} 
                          color={page.status === 'completed' ? 'success' : 'warning'} 
                          size="small" 
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Crawled: {formatDate(page.created_at)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePagesDialog}>Close</Button>
        </DialogActions>
      </Dialog>
      
      {/* View Document Dialog */}
      <Dialog open={viewingDocument} onClose={handleCloseDocumentDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedDocument?.filename || selectedDocument?.file_name || 'Document'}
        </DialogTitle>
        <DialogContent>
          {documentLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                <strong>File Type:</strong> {selectedDocument?.file_type} | 
                <strong> Size:</strong> {selectedDocument?.file_size ? `${(selectedDocument.file_size / 1024).toFixed(2)} KB` : 'Unknown'}
              </Typography>
              
              <Paper 
                variant="outlined" 
                sx={{ 
                  p: 2, 
                  maxHeight: '400px', 
                  overflow: 'auto',
                  bgcolor: 'grey.50',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }}
              >
                <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {documentContent}
                </Typography>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDocumentDialog}>Close</Button>
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
      
      {/* Delete Document Confirmation Dialog */}
      <Dialog open={openDeleteDocumentDialog} onClose={handleCloseDeleteDocumentDialog}>
        <DialogTitle>Confirm Document Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the document "{documentToDelete?.filename || documentToDelete?.file_name || 'Untitled Document'}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDocumentDialog}>Cancel</Button>
          <Button onClick={handleConfirmDeleteDocument} color="error" variant="contained">
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