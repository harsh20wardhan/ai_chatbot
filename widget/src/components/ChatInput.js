import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';

const Container = styled.div`
  padding: 12px;
  border-top: 1px solid ${({ theme }) => theme === 'dark' ? '#444' : '#eee'};
  background-color: ${({ theme }) => theme === 'dark' ? '#1e1e1e' : '#ffffff'};
`;

const Form = styled.form`
  display: flex;
  align-items: center;
`;

const Input = styled.input`
  flex: 1;
  padding: 10px 16px;
  border-radius: 20px;
  border: 1px solid ${({ theme }) => theme === 'dark' ? '#444' : '#ddd'};
  background-color: ${({ theme }) => theme === 'dark' ? '#333' : '#fff'};
  color: ${({ theme }) => theme === 'dark' ? '#fff' : '#000'};
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: ${({ primaryColor }) => primaryColor};
  }
  
  &::placeholder {
    color: ${({ theme }) => theme === 'dark' ? '#aaa' : '#999'};
  }
`;

const Button = styled.button`
  background-color: ${({ primaryColor }) => primaryColor};
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  margin-left: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    opacity: 0.9;
    transform: scale(1.05);
  }
  
  &:disabled {
    background-color: ${({ theme }) => theme === 'dark' ? '#555' : '#ccc'};
    cursor: not-allowed;
    opacity: 0.7;
    transform: none;
  }
  
  &:focus {
    outline: none;
  }
`;

// Send icon
const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2.01 21L23 12L2.01 3L2 10L17 12L2 14L2.01 21Z" fill="currentColor"/>
  </svg>
);

export default function ChatInput({ value, onChange, onSend, placeholder, theme, primaryColor }) {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef(null);
  
  // Focus input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim()) {
      onSend();
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      handleSubmit(e);
    }
  };
  
  return (
    <Container theme={theme}>
      <Form onSubmit={handleSubmit}>
        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          theme={theme}
          primaryColor={primaryColor}
          aria-label="Type your message"
        />
        <Button 
          type="submit"
          disabled={!value.trim()}
          primaryColor={primaryColor}
          theme={theme}
          aria-label="Send message"
        >
          <SendIcon />
        </Button>
      </Form>
    </Container>
  );
}