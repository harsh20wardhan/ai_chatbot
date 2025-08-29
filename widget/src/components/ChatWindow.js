import React, { useRef, useEffect } from 'react';
import styled from 'styled-components';
import { useWidget } from '../contexts/WidgetContext';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { sendMessage } from '../services/api';

const Container = styled.div`
  width: ${({ width }) => width}px;
  max-width: calc(100vw - 40px);
  height: ${({ height }) => height}px;
  max-height: calc(100vh - 100px);
  background-color: ${({ theme }) => theme === 'dark' ? '#1e1e1e' : '#ffffff'};
  color: ${({ theme }) => theme === 'dark' ? '#ffffff' : '#000000'};
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
  animation: slideIn 0.3s forwards;
  position: relative;
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const ResizeHandle = styled.div`
  position: absolute;
  right: 0;
  bottom: 0;
  width: 20px;
  height: 20px;
  cursor: se-resize;
  background: linear-gradient(-45deg, transparent 30%, ${({ theme, primaryColor }) => theme === 'dark' ? '#666' : primaryColor} 30%, ${({ theme, primaryColor }) => theme === 'dark' ? '#666' : primaryColor} 40%, transparent 40%);
  
  &:hover {
    background: linear-gradient(-45deg, transparent 30%, ${({ theme, primaryColor }) => theme === 'dark' ? '#888' : primaryColor} 30%, ${({ theme, primaryColor }) => theme === 'dark' ? '#888' : primaryColor} 40%, transparent 40%);
  }
`;

const Header = styled.div`
  background-color: ${({ primaryColor }) => primaryColor};
  color: white;
  padding: 16px;
  display: flex;
  align-items: center;
`;

const Logo = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-weight: 600;
`;

const Title = styled.div`
  font-size: 16px;
  font-weight: 500;
`;

const Content = styled.div`
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const LoadingContainer = styled.div`
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: ${({ theme }) => theme === 'dark' ? '#ffffff' : '#666666'};
`;

const ErrorContainer = styled.div`
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: #ff3b30;
  padding: 20px;
  text-align: center;
`;

const Spinner = styled.div`
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-top: 3px solid ${({ primaryColor }) => primaryColor};
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin-right: 10px;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

export default function ChatWindow({ loading, error }) {
  const { 
    config, 
    messages, 
    addMessage, 
    inputText, 
    setInputText,
    conversationId,
    setConversation,
    isTyping,
    setIsTyping
  } = useWidget();
  
  const messagesEndRef = useRef(null);
  const [dimensions, setDimensions] = React.useState({ width: 350, height: 500 });
  const isResizing = useRef(false);
  const startPos = useRef({ x: 0, y: 0 });
  const startSize = useRef({ width: 0, height: 0 });
  const audioRef = useRef(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Play notification sound when receiving messages
  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
      playNotificationSound();
    }
  }, [messages]);

  const playNotificationSound = () => {
    try {
      // Create a simple notification sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      console.log('Could not play notification sound:', error);
    }
  };

  // Handle resize functionality
  useEffect(() => {
    const handleMouseDown = (e) => {
      if (e.target.closest('[data-resize-handle]')) {
        isResizing.current = true;
        startPos.current = { x: e.clientX, y: e.clientY };
        startSize.current = { width: dimensions.width, height: dimensions.height };
        document.body.style.cursor = 'se-resize';
        document.body.style.userSelect = 'none';
      }
    };

    const handleMouseMove = (e) => {
      if (isResizing.current) {
        const deltaX = e.clientX - startPos.current.x;
        const deltaY = e.clientY - startPos.current.y;
        
        const newWidth = Math.max(300, Math.min(800, startSize.current.width + deltaX));
        const newHeight = Math.max(400, Math.min(800, startSize.current.height + deltaY));
        
        setDimensions({ width: newWidth, height: newHeight });
      }
    };

    const handleMouseUp = () => {
      if (isResizing.current) {
        isResizing.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [dimensions]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;
    
    // Add user message to chat
    addMessage({
      role: 'user',
      content: inputText,
    });
    
    // Clear input
    setInputText('');
    
    // Set typing indicator
    setIsTyping(true);
    
    try {
      // Send message to API
      const response = await sendMessage(
        config.botId,
        inputText,
        conversationId
      );
      
      // Store conversation ID if it's a new conversation
      if (!conversationId && response.conversation_id) {
        setConversation(response.conversation_id);
      }
      
      // Add bot response to chat
      addMessage({
        role: 'assistant',
        content: response.message,
        // Sources removed - sources will not be displayed
      });
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      addMessage({
        role: 'system',
        content: 'Sorry, there was an error processing your request. Please try again later.',
      });
    } finally {
      // Remove typing indicator
      setIsTyping(false);
    }
  };

  if (loading) {
    return (
      <Container theme={config.theme} width={dimensions.width} height={dimensions.height}>
        <Header primaryColor={config.primaryColor}>
          <Logo>AI</Logo>
          <Title>Loading...</Title>
        </Header>
        <LoadingContainer theme={config.theme}>
          <Spinner primaryColor={config.primaryColor} />
          <span>Loading chat...</span>
        </LoadingContainer>
        <ResizeHandle theme={config.theme} primaryColor={config.primaryColor} data-resize-handle />
      </Container>
    );
  }

  if (error) {
    return (
      <Container theme={config.theme} width={dimensions.width} height={dimensions.height}>
        <Header primaryColor={config.primaryColor}>
          <Logo>AI</Logo>
          <Title>Error</Title>
        </Header>
        <ErrorContainer>
          <div>
            <p>Sorry, there was an error loading the chat widget.</p>
            <p>{error}</p>
          </div>
        </ErrorContainer>
        <ResizeHandle theme={config.theme} primaryColor={config.primaryColor} data-resize-handle />
      </Container>
    );
  }

  return (
    <Container theme={config.theme} width={dimensions.width} height={dimensions.height}>
      <Header primaryColor={config.primaryColor}>
        <Logo>{config.name ? config.name.charAt(0).toUpperCase() : 'AI'}</Logo>
        <Title>{config.name || 'AI Assistant'}</Title>
      </Header>
      <Content>
        <MessageList 
          messages={messages} 
          isTyping={isTyping} 
          theme={config.theme}
          primaryColor={config.primaryColor}
          messagesEndRef={messagesEndRef}
        />
        <ChatInput 
          value={inputText}
          onChange={setInputText}
          onSend={handleSendMessage}
          placeholder={config.placeholderText || 'Ask me anything...'}
          theme={config.theme}
          primaryColor={config.primaryColor}
        />
      </Content>
      <ResizeHandle theme={config.theme} primaryColor={config.primaryColor} data-resize-handle />
    </Container>
  );
}