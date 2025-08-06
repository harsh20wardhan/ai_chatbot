import React from 'react';
import styled from 'styled-components';
import Message from './Message';

const Container = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  
  /* Scrollbar styling */
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: ${({ theme }) => theme === 'dark' ? '#333' : '#f1f1f1'};
  }
  
  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme === 'dark' ? '#666' : '#ccc'};
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: ${({ theme }) => theme === 'dark' ? '#888' : '#aaa'};
  }
`;

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${({ theme }) => theme === 'dark' ? '#999' : '#666'};
  font-size: 14px;
  text-align: center;
  padding: 20px;
`;

const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 8px 16px;
  border-radius: 18px;
  max-width: 80%;
  align-self: flex-start;
  background-color: ${({ theme }) => theme === 'dark' ? '#333' : '#f0f0f0'};
  color: ${({ theme }) => theme === 'dark' ? '#fff' : '#000'};
  font-size: 14px;
`;

const Dot = styled.span`
  width: 8px;
  height: 8px;
  margin: 0 2px;
  background-color: ${({ theme, primaryColor }) => theme === 'dark' ? '#fff' : primaryColor};
  border-radius: 50%;
  display: inline-block;
  opacity: 0.6;
  animation: bounce 1.4s infinite ease-in-out both;
  animation-delay: ${({ delay }) => delay}s;
  
  @keyframes bounce {
    0%, 80%, 100% {
      transform: scale(0);
    }
    40% {
      transform: scale(1);
    }
  }
`;

export default function MessageList({ 
  messages, 
  isTyping, 
  showSources,
  theme,
  primaryColor,
  messagesEndRef 
}) {
  return (
    <Container theme={theme}>
      {messages.length === 0 ? (
        <EmptyState theme={theme}>
          Start a conversation by sending a message.
        </EmptyState>
      ) : (
        messages.map((message, index) => (
          <Message
            key={message.id || index}
            message={message}
            showSources={showSources}
            theme={theme}
            primaryColor={primaryColor}
          />
        ))
      )}
      
      {isTyping && (
        <TypingIndicator theme={theme}>
          <Dot theme={theme} primaryColor={primaryColor} delay={0} />
          <Dot theme={theme} primaryColor={primaryColor} delay={0.2} />
          <Dot theme={theme} primaryColor={primaryColor} delay={0.4} />
        </TypingIndicator>
      )}
      
      <div ref={messagesEndRef} />
    </Container>
  );
}