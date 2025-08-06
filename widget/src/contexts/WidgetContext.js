import React, { createContext, useState, useContext, useEffect } from 'react';
import { fetchWidgetConfig } from '../services/api';

const WidgetContext = createContext();

export function useWidget() {
  return useContext(WidgetContext);
}

export function WidgetProvider({ children, initialConfig }) {
  const [config, setConfig] = useState(initialConfig);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);

  // Fetch widget configuration from API
  useEffect(() => {
    const loadConfig = async () => {
      if (!config.botId) {
        setError('No bot ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const widgetConfig = await fetchWidgetConfig(config.botId);
        
        setConfig(prev => ({
          ...prev,
          ...widgetConfig,
          // Keep the botId from initialConfig
          botId: prev.botId,
        }));
        
        // Add welcome message if available
        if (widgetConfig.welcome_message) {
          setMessages([
            {
              id: 'welcome',
              role: 'assistant',
              content: widgetConfig.welcome_message,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (err) {
        console.error('Error loading widget configuration:', err);
        setError('Failed to load widget configuration');
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [config.botId]);

  // Toggle widget open/closed
  const toggleWidget = () => {
    setIsOpen(prev => !prev);
  };

  // Add a new message to the chat
  const addMessage = (message) => {
    setMessages(prev => [...prev, {
      id: message.id || Date.now().toString(),
      role: message.role,
      content: message.content,
      timestamp: new Date(),
      sources: message.sources,
    }]);
  };

  // Clear all messages
  const clearMessages = () => {
    setMessages([]);
    setConversationId(null);
  };

  // Set the conversation ID
  const setConversation = (id) => {
    setConversationId(id);
  };

  const value = {
    config,
    setConfig,
    isOpen,
    setIsOpen,
    toggleWidget,
    loading,
    error,
    messages,
    addMessage,
    clearMessages,
    inputText,
    setInputText,
    conversationId,
    setConversation,
    isTyping,
    setIsTyping,
  };

  return (
    <WidgetContext.Provider value={value}>
      {children}
    </WidgetContext.Provider>
  );
}