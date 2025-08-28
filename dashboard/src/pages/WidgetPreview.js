import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Avatar,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Container,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Link as LinkIcon,
  Visibility as PreviewIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  ChatBubbleOutline as ChatBubbleIcon,
  Mouse as MouseIcon,
  HelpOutline as HelpIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { chatApi, widgetApi } from '../services/api';

export default function WidgetPreview() {
  const { botId } = useParams();
  const [bot, setBot] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Widget state
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);
  const [isWidgetMinimized, setIsWidgetMinimized] = useState(false);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);

  useEffect(() => {
    const fetchWidgetData = async () => {
      try {
        setLoading(true);
        
        // Fetch widget configuration
        const widgetConfig = await widgetApi.getWidgetConfig(botId);
        setConfig(widgetConfig);
        
        // Create a mock bot object for display
        setBot({
          id: botId,
          name: widgetConfig.name || 'AI Assistant',
          description: 'Powered by RAG-enabled AI'
        });
        
      } catch (err) {
        console.error('Error fetching widget data:', err);
        setError('Failed to load widget configuration');
      } finally {
        setLoading(false);
      }
    };

    fetchWidgetData();
  }, [botId]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || sending) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setSending(true);

    try {
      // Send message to RAG-enabled chat API
      const response = await chatApi.sendMessage(
        botId,
        inputMessage,
        conversationId,
        true // Enable RAG
      );

      const botMessage = {
        id: Date.now() + 1,
        content: response.answer,
        sender: 'bot',
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Update conversation ID if this is a new conversation
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage = {
        id: Date.now() + 1,
        content: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date().toISOString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const addMessage = (content, sender, sources = []) => {
    const message = {
      id: Date.now(),
      content,
      sender,
      timestamp: new Date().toISOString(),
      sources
    };
    setMessages(prev => [...prev, message]);
  };

  const toggleWidget = () => {
    setIsWidgetOpen(!isWidgetOpen);
  };

  const minimizeWidget = () => {
    setIsWidgetMinimized(!isWidgetMinimized);
  };

  const copyEmbedCode = () => {
    const embedCode = `<script>
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
    
    navigator.clipboard.writeText(embedCode);
    // You could add a snackbar notification here
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        bgcolor: 'background.default'
      }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: 2
      }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={() => window.history.back()}>
          Go Back
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      minHeight: '100vh',
      bgcolor: 'background.default',
      position: 'relative'
    }}>
      {/* Main Content */}
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Grid container spacing={4} alignItems="stretch">
          {/* Header Section */}
          <Grid item xs={12}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar sx={{ bgcolor: config?.primary_color || '#2563eb' }}>
                    <BotIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h4" gutterBottom>
                      {bot?.name}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Widget Preview Mode
                    </Typography>
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  This is how your AI chatbot widget will appear when embedded on a website. 
                  The widget will be positioned in the bottom-right corner and can be opened/closed by users.
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    startIcon={<CodeIcon />}
                    onClick={copyEmbedCode}
                  >
                    Copy Embed Code
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<SettingsIcon />}
                    onClick={() => window.history.back()}
                  >
                    Back to Configuration
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Instructions Section */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flex: 1 }}>
                <Typography variant="h6" gutterBottom>
                  How to Test
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><MouseIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Open the chat from the bottom-right launcher"
                      secondary="Simulates the user experience on your website"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><HelpIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Ask questions based on your content"
                      secondary="Responses are grounded with sources via RAG"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><ExpandMoreIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Try minimize / expand"
                      secondary="The window can be minimized to stay out of the way"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><LinkIcon /></ListItemIcon>
                    <ListItemText 
                      primary="Review source attribution"
                      secondary="Each answer includes source snippets for auditability"
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Widget Features */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flex: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Widget Features
                </Typography>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr 1fr', sm: '1fr 1fr' },
                    gap: 2,
                  }}
                >
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      background:
                        'linear-gradient(180deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 100%)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <BotIcon color="primary" />
                      <Typography variant="subtitle2" fontWeight={700}>
                        RAG-enabled AI
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Answers grounded in your data sources
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      background:
                        'linear-gradient(180deg, rgba(34,197,94,0.06) 0%, rgba(34,197,94,0.02) 100%)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <LinkIcon color="success" />
                      <Typography variant="subtitle2" fontWeight={700}>
                        Source Attribution
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Transparent citations for every answer
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      background:
                        'linear-gradient(180deg, rgba(14,165,233,0.06) 0%, rgba(14,165,233,0.02) 100%)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <PreviewIcon color="info" />
                      <Typography variant="subtitle2" fontWeight={700}>
                        Responsive Design
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Looks great on desktop and mobile
                    </Typography>
                  </Box>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: '1px solid',
                      borderColor: 'divider',
                      background:
                        'linear-gradient(180deg, rgba(34,197,94,0.06) 0%, rgba(34,197,94,0.02) 100%)',
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <SettingsIcon color="secondary" />
                      <Typography variant="subtitle2" fontWeight={700}>
                        Customizable Theme
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Match your brand in minutes
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Embedded Widget */}
          <Box sx={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        zIndex: 9999,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: '14px',
        lineHeight: 1.4,
      }}>
        
        {/* Chat Window */}
          <Box sx={{
          display: isWidgetOpen ? 'flex' : 'none',
          flexDirection: 'column',
          width: 350,
          height: isWidgetMinimized ? 60 : 500,
           bgcolor: config?.theme === 'dark' ? '#1f2937' : '#ffffff',
          borderRadius: 3,
           boxShadow: '0 10px 30px rgba(2, 6, 23, 0.12)',
           border: `1px solid ${config?.theme === 'dark' ? '#374151' : '#e2e8f0'}`,
          overflow: 'hidden',
          transition: 'height 0.3s ease',
        }}>
          
          {/* Header */}
          <Box sx={{
            background: `linear-gradient(135deg, ${config?.primary_color || '#2563eb'} 0%, #0ea5e9 100%)`,
            color: 'white',
            px: 2,
            py: isWidgetMinimized ? 1 : 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: isWidgetMinimized ? 60 : 'auto',
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar sx={{ 
                width: isWidgetMinimized ? 28 : 32, 
                height: isWidgetMinimized ? 28 : 32, 
                bgcolor: 'rgba(255, 255, 255, 0.2)'
              }}>
                <BotIcon fontSize={isWidgetMinimized ? 'small' : 'medium'} />
              </Avatar>
              <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography variant="body1" sx={{ fontWeight: 600, lineHeight: 1 }}>
                  {bot?.name}
                </Typography>
                {!isWidgetMinimized && (
                  <Typography variant="caption" sx={{ opacity: 0.8, lineHeight: 1 }}>
                    RAG-enabled AI
                  </Typography>
                )}
              </Box>
            </Box>
            <IconButton
              onClick={minimizeWidget}
              sx={{ color: 'white', p: 0.5 }}
            >
              {isWidgetMinimized ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          
          {/* Messages Area */}
          {!isWidgetMinimized && (
            <Box sx={{
              flex: 1,
              overflow: 'auto',
              p: 2,
              bgcolor: config?.theme === 'dark' ? '#111827' : '#f8fafc',
            }}>
              {messages.length === 0 ? (
                <Box sx={{
                  textAlign: 'center',
                  color: config?.theme === 'dark' ? '#cbd5e1' : '#64748b',
                  mb: 2,
                }}>
                  <Avatar sx={{ width: 56, height: 56, mx: 'auto', mb: 1, bgcolor: config?.primary_color || 'primary.main' }}>
                    <BotIcon />
                  </Avatar>
                  <Typography variant="body1" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {config?.welcome_message || 'Hi there! How can I help you today?'}
                  </Typography>
                  <Typography variant="caption">
                    Answers are grounded in your documents and websites with source links.
                  </Typography>
                </Box>
              ) : (
                messages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      mb: 2,
                      display: 'flex',
                      justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                    }}
                  >
                    <Box sx={{
                      maxWidth: '80%',
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: message.sender === 'user'
                        ? (config?.primary_color || '#2563eb')
                        : (config?.theme === 'dark' ? '#374151' : '#ffffff'),
                      color: message.sender === 'user' ? 'white' : (config?.theme === 'dark' ? 'white' : 'inherit'),
                      boxShadow: '0 6px 24px rgba(2, 6, 23, 0.08)',
                      wordWrap: 'break-word',
                    }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {message.content}
                      </Typography>
                      
                      {/* Sources display removed - sources will not be shown */}
                    </Box>
                  </Box>
                ))
              )}
              
              {sending && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <Box sx={{
                    p: 1.5,
                    borderRadius: 2,
                    bgcolor: config?.theme === 'dark' ? '#374151' : '#ffffff',
                    color: config?.theme === 'dark' ? 'white' : 'inherit',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                  }}>
                    <CircularProgress size={16} />
                  </Box>
                </Box>
              )}
            </Box>
          )}
          
          {/* Input Area */}
          {!isWidgetMinimized && (
            <Box sx={{
              p: 2,
              bgcolor: config?.theme === 'dark' ? '#1f2937' : '#ffffff',
              borderTop: `1px solid ${config?.theme === 'dark' ? '#374151' : '#e2e8f0'}`,
            }}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <input
                  type="text"
                  placeholder={config?.placeholder_text || 'Ask me anything...'}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={sending}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: `1px solid ${config?.theme === 'dark' ? '#555' : '#ddd'}`,
                    borderRadius: '8px',
                    background: config?.theme === 'dark' ? '#1e1e1e' : '#ffffff',
                    color: config?.theme === 'dark' ? '#ffffff' : '#000000',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || sending}
                  sx={{
                    minWidth: 48,
                    borderRadius: 2,
                    bgcolor: config?.primary_color || '#2563eb',
                    '&:hover': {
                      bgcolor: config?.primary_color || '#2563eb',
                      opacity: 0.9
                    }
                  }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Box>
          )}
        </Box>
        
        {/* Chat Button */}
        <Button
          onClick={toggleWidget}
          sx={{
            width: 60,
            height: 60,
            bgcolor: config?.primary_color || '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '50%',
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
            fontSize: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'transform 0.2s',
            '&:hover': {
              transform: 'scale(1.05)',
              bgcolor: config?.primary_color || '#2563eb',
            }
          }}
        >
          {isWidgetOpen ? <ExpandMoreIcon /> : <ChatBubbleIcon />}
        </Button>
      </Box>
    </Box>
  );
} 