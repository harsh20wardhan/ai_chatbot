import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
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
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as UserIcon,
  Link as LinkIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';
import { chatApi, widgetApi } from '../services/api';

export default function WidgetPreview() {
  const { botId } = useParams();
  const [bot, setBot] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
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
        content: response.answer, // Changed from response.message to response.answer
        sender: 'bot',
        timestamp: new Date().toISOString(),
        sources: response.sources || []
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Update conversation ID if this is a new conversation
      if (!conversationId && response.conversation_id) { // Changed from response.conversationId
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

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        bgcolor: config?.theme === 'dark' ? '#1e1e1e' : '#f5f5f5'
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
      height: '100vh',
      bgcolor: config?.theme === 'dark' ? '#1e1e1e' : '#f5f5f5',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Header */}
      <Paper 
        elevation={2}
        sx={{ 
          p: 2, 
          borderRadius: 0,
          bgcolor: config?.primary_color || '#3f51b5',
          color: 'white'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
            <BotIcon />
          </Avatar>
          <Box>
            <Typography variant="h6">{bot?.name}</Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              RAG-enabled AI Assistant
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Chat Area */}
      <Box sx={{ 
        flex: 1, 
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Messages */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}>
          {messages.length === 0 ? (
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              color: config?.theme === 'dark' ? 'white' : 'text.secondary'
            }}>
              <BotIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" gutterBottom>
                {config?.welcome_message || `Hi there! I'm ${bot?.name}. How can I help you today?`}
              </Typography>
              <Typography variant="body2" sx={{ maxWidth: 400 }}>
                I can answer questions based on your uploaded documents and crawled websites. 
                Try asking me anything!
              </Typography>
            </Box>
          ) : (
            messages.map((message) => (
              <Box
                key={message.id}
                sx={{
                  display: 'flex',
                  justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2
                }}
              >
                <Card
                  sx={{
                    maxWidth: '70%',
                    bgcolor: message.sender === 'user' 
                      ? (config?.primary_color || '#3f51b5')
                      : (config?.theme === 'dark' ? '#2d2d2d' : 'white'),
                    color: message.sender === 'user' ? 'white' : 'inherit',
                    borderRadius: 2,
                    position: 'relative'
                  }}
                >
                  <CardContent sx={{ pb: message.sources?.length ? 1 : 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                      <Avatar 
                        sx={{ 
                          width: 24, 
                          height: 24,
                          bgcolor: message.sender === 'user' 
                            ? 'rgba(255,255,255,0.2)' 
                            : (config?.primary_color || '#3f51b5')
                        }}
                      >
                        {message.sender === 'user' ? <UserIcon /> : <BotIcon />}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                          {message.content}
                        </Typography>
                        {message.error && (
                          <Typography variant="caption" sx={{ color: 'error.main', mt: 1 }}>
                            Error occurred
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                  
                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <Box sx={{ px: 2, pb: 2 }}>
                      <Divider sx={{ mb: 1 }} />
                      <Typography variant="caption" sx={{ opacity: 0.7, mb: 1, display: 'block' }}>
                        Sources:
                      </Typography>
                      <List dense sx={{ py: 0 }}>
                        {message.sources.map((source, index) => {
                          // Extract first 3-4 words from the text
                          const words = (source.text || source.title || '').split(' ');
                          const shortText = words.slice(0, 3).join(' ') + (words.length > 3 ? '...' : '');
                          
                          return (
                            <ListItem key={index} sx={{ py: 0, px: 0 }}>
                              <ListItemIcon sx={{ minWidth: 20 }}>
                                <LinkIcon sx={{ fontSize: 16 }} />
                              </ListItemIcon>
                              <ListItemText
                                primary={shortText}
                                primaryTypographyProps={{ variant: 'caption' }}
                              />
                            </ListItem>
                          );
                        })}
                      </List>
                    </Box>
                  )}
                </Card>
              </Box>
            ))
          )}
          
          {sending && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <Card sx={{ bgcolor: config?.theme === 'dark' ? '#2d2d2d' : 'white' }}>
                <CardContent sx={{ py: 1, px: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" sx={{ opacity: 0.7 }}>
                      Thinking...
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>

        {/* Input Area */}
        <Paper 
          elevation={3}
          sx={{ 
            p: 2, 
            borderRadius: 0,
            bgcolor: config?.theme === 'dark' ? '#2d2d2d' : 'white'
          }}
        >
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder={config?.placeholder_text || 'Ask me anything...'}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={sending}
              size="small"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || sending}
              sx={{
                minWidth: 48,
                borderRadius: 2,
                bgcolor: config?.primary_color || '#3f51b5',
                '&:hover': {
                  bgcolor: config?.primary_color || '#3f51b5',
                  opacity: 0.9
                }
              }}
            >
              <SendIcon />
            </Button>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
} 