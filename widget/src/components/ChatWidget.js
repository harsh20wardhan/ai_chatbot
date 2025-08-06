import React, { useRef, useEffect } from 'react';
import styled, { createGlobalStyle } from 'styled-components';
import { useWidget } from '../contexts/WidgetContext';
import ChatButton from './ChatButton';
import ChatWindow from './ChatWindow';

// Global styles to ensure widget doesn't inherit styles from the parent website
const GlobalStyle = createGlobalStyle`
  #ai-chatbot-widget-container * {
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    line-height: 1.5;
  }
`;

// Main container for the widget
const WidgetContainer = styled.div`
  position: fixed;
  ${({ position }) => position === 'bottom-right' ? 'right: 20px;' : 'left: 20px;'}
  bottom: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: ${({ position }) => position === 'bottom-right' ? 'flex-end' : 'flex-start'};
`;

export default function ChatWidget() {
  const { 
    config, 
    isOpen, 
    toggleWidget,
    loading,
    error
  } = useWidget();
  
  const containerRef = useRef(null);

  // Close widget when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target) && isOpen) {
        toggleWidget();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, toggleWidget]);

  // Don't render if there's no bot ID
  if (!config.botId) {
    console.error('AI Chatbot Widget: No bot ID provided');
    return null;
  }

  return (
    <>
      <GlobalStyle />
      <WidgetContainer 
        position={config.position} 
        ref={containerRef}
      >
        {isOpen && (
          <ChatWindow 
            loading={loading}
            error={error}
          />
        )}
        <ChatButton onClick={toggleWidget} isOpen={isOpen} />
      </WidgetContainer>
    </>
  );
}