import React from 'react';
import styled from 'styled-components';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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



// Filter out thinking and reasoning tags from AI responses
const filterAIResponse = (content) => {
  if (!content || typeof content !== 'string') {
    return content;
  }
  
  // Remove <thinking>...</thinking> blocks
  content = content.replace(/<thinking[^>]*>[\s\S]*?<\/thinking>/gi, '');
  
  // Remove <reasoning>...</reasoning> blocks
  content = content.replace(/<reasoning[^>]*>[\s\S]*?<\/reasoning>/gi, '');
  
  // Clean up any extra whitespace or line breaks left behind
  content = content.replace(/\n\s*\n/g, '\n').trim();
  
  return content;
};

const MarkdownContent = styled.div`
  h1, h2, h3, h4, h5, h6 {
    margin: 0.5em 0 0.3em 0;
    font-weight: 600;
  }
  
  p {
    margin: 0.5em 0;
    line-height: 1.4;
  }
  
  ul, ol {
    margin: 0.5em 0;
    padding-left: 1.5em;
  }
  
  li {
    margin: 0.2em 0;
  }
  
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.5em 0;
    font-size: 0.9em;
  }
  
  th, td {
    border: 1px solid ${({ theme }) => theme === 'dark' ? '#555' : '#ddd'};
    padding: 0.5em;
    text-align: left;
  }
  
  th {
    background-color: ${({ theme }) => theme === 'dark' ? '#444' : '#f5f5f5'};
    font-weight: 600;
  }
  
  code {
    background-color: ${({ theme }) => theme === 'dark' ? '#333' : '#f0f0f0'};
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
  
  pre {
    background-color: ${({ theme }) => theme === 'dark' ? '#333' : '#f0f0f0'};
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
    margin: 0.5em 0;
  }
  
  blockquote {
    border-left: 4px solid ${({ theme, primaryColor }) => theme === 'dark' ? '#555' : primaryColor};
    margin: 0.5em 0;
    padding-left: 1em;
    font-style: italic;
  }
  
  strong {
    font-weight: 600;
  }
  
  em {
    font-style: italic;
  }
`;

export default function Message({ message, theme, primaryColor }) {
  
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  

  
  // Filter the message content if it's from the AI
  const displayContent = message.role === 'assistant' || message.role === 'bot' 
    ? filterAIResponse(message.content) 
    : message.content;
  
  return (
    <MessageContainer role={message.role}>
      <MessageBubble 
        role={message.role}
        theme={theme}
        primaryColor={primaryColor}
      >
        {message.role === 'user' ? (
          displayContent
        ) : (
          <MarkdownContent theme={theme} primaryColor={primaryColor}>
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                // Customize link rendering to open in new tab
                a: ({node, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer" />
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </MarkdownContent>
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