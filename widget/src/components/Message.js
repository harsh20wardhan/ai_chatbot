import React, { useState } from 'react';
import styled from 'styled-components';

const MessageContainer = styled.div`
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
  max-width: 85%;
  align-self: ${({ role }) => role === 'user' ? 'flex-end' : 'flex-start'};
`;

const MessageBubble = styled.div`
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  background-color: ${({ role, theme, primaryColor }) => {
    if (role === 'user') return primaryColor;
    if (role === 'system') return theme === 'dark' ? '#ff6b6b' : '#ffeded';
    return theme === 'dark' ? '#333' : '#f0f0f0';
  }};
  color: ${({ role, theme }) => {
    if (role === 'user') return '#fff';
    if (role === 'system') return theme === 'dark' ? '#fff' : '#d32f2f';
    return theme === 'dark' ? '#fff' : '#000';
  }};
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
`;

const MessageTime = styled.div`
  font-size: 11px;
  color: ${({ theme }) => theme === 'dark' ? '#aaa' : '#888'};
  margin-top: 4px;
  align-self: ${({ role }) => role === 'user' ? 'flex-end' : 'flex-start'};
`;

const SourcesContainer = styled.div`
  margin-top: 8px;
  font-size: 12px;
  color: ${({ theme }) => theme === 'dark' ? '#aaa' : '#666'};
`;

const SourcesToggle = styled.button`
  background: none;
  border: none;
  color: ${({ theme, primaryColor }) => theme === 'dark' ? '#fff' : primaryColor};
  font-size: 12px;
  padding: 0;
  margin: 0;
  cursor: pointer;
  text-decoration: underline;
  
  &:hover {
    opacity: 0.8;
  }
`;

const SourcesList = styled.ul`
  margin: 8px 0 0;
  padding-left: 20px;
`;

const SourceItem = styled.li`
  margin-bottom: 4px;
`;

const SourceLink = styled.a`
  color: ${({ theme, primaryColor }) => theme === 'dark' ? '#fff' : primaryColor};
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
`;

export default function Message({ message, showSources, theme, primaryColor }) {
  const [showSourcesList, setShowSourcesList] = useState(false);
  
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const toggleSources = () => {
    setShowSourcesList(!showSourcesList);
  };
  
  const hasSources = message.sources && message.sources.length > 0;
  
  return (
    <MessageContainer role={message.role}>
      <MessageBubble 
        role={message.role}
        theme={theme}
        primaryColor={primaryColor}
      >
        {message.content}
        
        {showSources && hasSources && (
          <SourcesContainer theme={theme}>
            <SourcesToggle 
              onClick={toggleSources}
              theme={theme}
              primaryColor={primaryColor}
            >
              {showSourcesList ? 'Hide sources' : 'Show sources'}
            </SourcesToggle>
            
            {showSourcesList && (
              <SourcesList>
                {message.sources.map((source, index) => (
                  <SourceItem key={index}>
                    <SourceLink 
                      href={source.url} 
                      target="_blank"
                      rel="noopener noreferrer"
                      theme={theme}
                      primaryColor={primaryColor}
                    >
                      {source.title || source.url}
                    </SourceLink>
                  </SourceItem>
                ))}
              </SourcesList>
            )}
          </SourcesContainer>
        )}
      </MessageBubble>
      
      <MessageTime 
        role={message.role}
        theme={theme}
      >
        {formatTime(message.timestamp)}
      </MessageTime>
    </MessageContainer>
  );
}