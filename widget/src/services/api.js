import axios from 'axios';

// Default API URL - this should be configurable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8787/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Fetch widget configuration for a bot
 * @param {string} botId - The bot ID
 * @returns {Promise<Object>} - Widget configuration
 */
export const fetchWidgetConfig = async (botId) => {
  try {
    const response = await api.get(`/widget/${botId}/config`);
    return response.data.config;
  } catch (error) {
    console.error('Error fetching widget config:', error);
    throw error;
  }
};

/**
 * Send a message to the bot
 * @param {string} botId - The bot ID
 * @param {string} message - The message text
 * @param {string|null} conversationId - Optional conversation ID for continuing a conversation
 * @returns {Promise<Object>} - Bot response
 */
export const sendMessage = async (botId, message, conversationId = null) => {
  try {
    const response = await api.post('/chat', {
      bot_id: botId,
      message,
      conversation_id: conversationId,
      use_rag: true,
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

/**
 * Get conversation history
 * @param {string} conversationId - The conversation ID
 * @returns {Promise<Object>} - Conversation history
 */
export const getConversation = async (conversationId) => {
  try {
    const response = await api.get(`/chat/conversations/${conversationId}`);
    return response.data.conversation;
  } catch (error) {
    console.error('Error fetching conversation:', error);
    throw error;
  }
};

export default api;