import React from 'react';
import styled from 'styled-components';
import { useWidget } from '../contexts/WidgetContext';

const Button = styled.button`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background-color: ${({ primaryColor }) => primaryColor};
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  margin-top: 16px;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  }
  
  &:focus {
    outline: none;
  }
`;

// Chat icon (open state)
const ChatIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2ZM20 16H5.17L4 17.17V4H20V16Z" fill="currentColor"/>
    <path d="M7 9H17V11H7V9ZM7 6H17V8H7V6ZM7 12H14V14H7V12Z" fill="currentColor"/>
  </svg>
);

// Close icon (close state)
const CloseIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="currentColor"/>
  </svg>
);

export default function ChatButton({ onClick, isOpen }) {
  const { config } = useWidget();
  
  return (
    <Button 
      onClick={onClick}
      primaryColor={config.primaryColor}
      aria-label={isOpen ? 'Close chat' : 'Open chat'}
    >
      {isOpen ? <CloseIcon /> : <ChatIcon />}
    </Button>
  );
}