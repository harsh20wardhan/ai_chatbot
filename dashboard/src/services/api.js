import axios from 'axios';

// Create an axios instance with base URL
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8787/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Don't send cookies with requests
});

// Debug environment variables
console.log('Dashboard API Configuration:');
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('Base URL being used:', api.defaults.baseURL);

// Add auth token to requests
api.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('auth_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Error data:', error.response.data);
      console.error('Error status:', error.response.status);
      console.error('Error headers:', error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Error request:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error message:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// API methods for bots
export const botApi = {
  // Get all bots
  getBots: async () => {
    const response = await api.get('/bots');
    return response.data.bots;
  },
  
  // Get a specific bot
  getBot: async (botId) => {
    const response = await api.get(`/bots/${botId}`);
    return response.data.bot;
  },
  
  // Create a new bot
  createBot: async (botData) => {
    const response = await api.post('/bots', botData);
    return response.data.bot;
  },
  
  // Update a bot
  updateBot: async (botId, botData) => {
    const response = await api.put(`/bots/${botId}`, botData);
    return response.data.bot;
  },
  
  // Delete a bot
  deleteBot: async (botId) => {
    const response = await api.delete(`/bots/${botId}`);
    return response.data;
  },
};

// API methods for widget configuration
export const widgetApi = {
  // Get widget configuration
  getWidgetConfig: async (botId) => {
    const response = await api.get(`/widget/${botId}/config`);
    return response.data.config;
  },
  
  // Update widget configuration
  updateWidgetConfig: async (botId, configData) => {
    const response = await api.post(`/widget/${botId}/config`, configData);
    return response.data.config;
  },
};

// API methods for documents
export const documentApi = {
  // Get all documents for a bot
  getDocuments: async (botId) => {
    const response = await api.get(`/documents?botId=${botId}`);
    return response.data.documents;
  },
  
  // Upload a document
  uploadDocument: async (botId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('botId', botId);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  // Delete a document
  deleteDocument: async (documentId) => {
    const response = await api.delete(`/documents/${documentId}`);
    return response.data;
  },
};

// API methods for crawling
export const crawlApi = {
  // Start a crawl job
  startCrawl: async (botId, url, maxDepth = 3, excludePatterns = []) => {
    const response = await api.post('/crawl/website', {
      botId: botId,
      url,
      maxDepth: maxDepth,
      excludePatterns: excludePatterns,
    });
    
    return response.data;
  },
  
  // Get crawl job status
  getCrawlStatus: async (jobId) => {
    const response = await api.get(`/crawl/status/${jobId}`);
    return response.data;
  },

  // Get all crawl jobs for a specific bot
  getCrawlJobsByBot: async (botId) => {
    const response = await api.get(`/crawl/jobs?botId=${botId}`);
    return response.data.jobs;
  },
  
  // Start a realtime crawl job
  startRealtimeCrawl: async (botId, url, maxDepth = 3, excludePatterns = []) => {
    const response = await api.post('/realtime-crawl/start', {
      botId: botId,
      url,
      maxDepth: maxDepth,
      excludePatterns: excludePatterns,
    });
    
    return response.data;
  },
  
  // Get realtime crawl job status
  getRealtimeCrawlStatus: async (jobId) => {
    const response = await api.get(`/realtime-crawl/status/${jobId}`);
    return response.data;
  },

  // Get all realtime crawl jobs for a specific bot
  getRealtimeCrawlJobsByBot: async (botId) => {
    const response = await api.get(`/realtime-crawl/jobs?botId=${botId}`);
    return response.data.jobs;
  },
};

// API methods for chat
export const chatApi = {
  // Send a message to the bot
  sendMessage: async (botId, message, conversationId = null, useRag = true) => {
    const response = await api.post('/chat', {
      botId: botId,
      query: message, // Changed from 'message' to 'query' to match backend
      conversationId: conversationId,
      useRag: useRag,
    });
    
    return response.data;
  },
  
  // Get conversations
  getConversations: async (botId) => {
    const response = await api.get(`/chat/conversations?botId=${botId}`);
    return response.data.conversations;
  },
  
  // Get a specific conversation
  getConversation: async (conversationId) => {
    const response = await api.get(`/chat/conversations/${conversationId}`);
    return response.data.conversation;
  },
};

// API methods for analytics
export const analyticsApi = {
  // Get bot usage statistics
  getBotStats: async (botId) => {
    // This would be a real endpoint in a production environment
    // For now, we'll return mock data
    return {
      totalMessages: 1250,
      uniqueUsers: 78,
      averageResponseTime: 1.2, // seconds
      topQuestions: [
        { question: "What are your business hours?", count: 45 },
        { question: "How do I reset my password?", count: 32 },
        { question: "What payment methods do you accept?", count: 28 },
        { question: "How do I contact support?", count: 21 },
        { question: "Do you offer refunds?", count: 17 }
      ],
      dailyUsage: [
        { date: '2023-05-01', messages: 42 },
        { date: '2023-05-02', messages: 38 },
        { date: '2023-05-03', messages: 56 },
        { date: '2023-05-04', messages: 61 },
        { date: '2023-05-05', messages: 47 },
        { date: '2023-05-06', messages: 28 },
        { date: '2023-05-07', messages: 32 }
      ]
    };
  }
};

export default api;