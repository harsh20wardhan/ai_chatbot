(function() {
  'use strict';
  
  // Widget configuration
  const config = {
    position: 'bottom-right', // bottom-right, bottom-left
    theme: 'light', // light, dark
    primaryColor: '#3f51b5',
    welcomeMessage: 'Hi there! How can I help you today?',
    placeholderText: 'Ask me anything...',
    showSources: true,
    autoOpenDelay: 0, // 0 = disabled
    zIndex: 9999
  };
  
  // Widget state
  let isOpen = false;
  let isMinimized = false;
  let messages = [];
  let conversationId = null;
  let botId = null;
  
  // Get bot ID from script tag
  const scriptTag = document.getElementById('ai-chatbot-widget');
  if (scriptTag && scriptTag.dataset.botId) {
    botId = scriptTag.dataset.botId;
  }
  
  // API base URL - use the API gateway directly
  const getApiUrl = () => {
    return 'http://localhost:8787/api';
  };
  
  // Create widget HTML
  function createWidget() {
    const widgetHTML = `
      <div id="ai-chatbot-widget-container" style="
        position: fixed;
        ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
        bottom: 20px;
        z-index: ${config.zIndex};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        line-height: 1.4;
      ">
        
        <!-- Chat Window -->
        <div id="ai-chatbot-chat-window" style="
          display: none;
          width: 350px;
          height: 500px;
          background: ${config.theme === 'dark' ? '#2d2d2d' : '#ffffff'};
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
          border: 1px solid ${config.theme === 'dark' ? '#444' : '#e0e0e0'};
          overflow: hidden;
          flex-direction: column;
        ">
          
          <!-- Header -->
          <div style="
            background: ${config.primaryColor};
            color: white;
            padding: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          ">
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="
                width: 32px;
                height: 32px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
              ">🤖</div>
              <div>
                <div style="font-weight: 600; font-size: 16px;">AI Assistant</div>
                <div style="font-size: 12px; opacity: 0.8;">RAG-enabled AI</div>
              </div>
            </div>
            <button id="ai-chatbot-minimize" style="
              background: none;
              border: none;
              color: white;
              cursor: pointer;
              font-size: 18px;
              padding: 4px;
            ">−</button>
          </div>
          
          <!-- Messages Area -->
          <div id="ai-chatbot-messages" style="
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: ${config.theme === 'dark' ? '#1e1e1e' : '#f8f9fa'};
          ">
            <div id="ai-chatbot-welcome" style="
              text-align: center;
              color: ${config.theme === 'dark' ? '#ccc' : '#666'};
              margin-bottom: 16px;
            ">
              <div style="font-size: 48px; margin-bottom: 8px;">🤖</div>
              <div style="font-weight: 600; margin-bottom: 8px;">${config.welcomeMessage}</div>
              <div style="font-size: 12px;">I can answer questions based on your documents and websites.</div>
            </div>
          </div>
          
          <!-- Input Area -->
          <div style="
            padding: 16px;
            background: ${config.theme === 'dark' ? '#2d2d2d' : '#ffffff'};
            border-top: 1px solid ${config.theme === 'dark' ? '#444' : '#e0e0e0'};
          ">
            <div style="display: flex; gap: 8px;">
              <input id="ai-chatbot-input" type="text" placeholder="${config.placeholderText}" style="
                flex: 1;
                padding: 12px;
                border: 1px solid ${config.theme === 'dark' ? '#555' : '#ddd'};
                border-radius: 8px;
                background: ${config.theme === 'dark' ? '#1e1e1e' : '#ffffff'};
                color: ${config.theme === 'dark' ? '#ffffff' : '#000000'};
                font-size: 14px;
                outline: none;
              ">
              <button id="ai-chatbot-send" style="
                padding: 12px 16px;
                background: ${config.primaryColor};
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
              ">Send</button>
            </div>
          </div>
        </div>
        
        <!-- Chat Button -->
        <button id="ai-chatbot-toggle" style="
          width: 60px;
          height: 60px;
          background: ${config.primaryColor};
          color: white;
          border: none;
          border-radius: 50%;
          cursor: pointer;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
          font-size: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s;
        ">💬</button>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
  }
  
  // Add message to chat
  function addMessage(content, sender, sources = []) {
    const messagesContainer = document.getElementById('ai-chatbot-messages');
    const welcomeDiv = document.getElementById('ai-chatbot-welcome');
    
    // Hide welcome message after first message
    if (welcomeDiv) {
      welcomeDiv.style.display = 'none';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
      margin-bottom: 16px;
      display: flex;
      justify-content: ${sender === 'user' ? 'flex-end' : 'flex-start'};
    `;
    
    const messageBubble = document.createElement('div');
    messageBubble.style.cssText = `
      max-width: 80%;
      padding: 12px 16px;
      border-radius: 12px;
      background: ${sender === 'user' ? config.primaryColor : (config.theme === 'dark' ? '#444' : '#ffffff')};
      color: ${sender === 'user' ? 'white' : (config.theme === 'dark' ? 'white' : 'black')};
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      word-wrap: break-word;
    `;
    
    messageBubble.textContent = content;
    messageDiv.appendChild(messageBubble);
    
    // Add sources if available
    if (sources && sources.length > 0 && config.showSources) {
      const sourcesDiv = document.createElement('div');
      sourcesDiv.style.cssText = `
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid ${config.theme === 'dark' ? '#555' : '#eee'};
        font-size: 12px;
        color: ${config.theme === 'dark' ? '#aaa' : '#666'};
      `;
      
      const sourcesTitle = document.createElement('div');
      sourcesTitle.textContent = 'Sources:';
      sourcesTitle.style.marginBottom = '4px';
      sourcesDiv.appendChild(sourcesTitle);
      
      sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.style.cssText = `
          display: flex;
          align-items: center;
          gap: 4px;
          margin-bottom: 2px;
        `;
        
        const linkIcon = document.createElement('span');
        linkIcon.textContent = '🔗';
        linkIcon.style.fontSize = '10px';
        
        const sourceText = document.createElement('span');
        const words = (source.text || source.title || '').split(' ');
        sourceText.textContent = words.slice(0, 3).join(' ') + (words.length > 3 ? '...' : '');
        
        sourceDiv.appendChild(linkIcon);
        sourceDiv.appendChild(sourceText);
        sourcesDiv.appendChild(sourceDiv);
      });
      
      messageBubble.appendChild(sourcesDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  // Send message to API
  async function sendMessage(message) {
    try {
      const response = await fetch(`${getApiUrl()}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          botId: botId,
          query: message,
          conversationId: conversationId,
          useRag: true
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add bot response
      addMessage(data.answer, 'bot', data.sources);
      
      // Update conversation ID
      if (data.conversation_id) {
        conversationId = data.conversation_id;
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    }
  }
  
  // Handle send button click
  function handleSend() {
    const input = document.getElementById('ai-chatbot-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addMessage(message, 'user');
    
    // Clear input
    input.value = '';
    
    // Send to API
    sendMessage(message);
  }
  
  // Toggle chat window
  function toggleChat() {
    const chatWindow = document.getElementById('ai-chatbot-chat-window');
    const toggleButton = document.getElementById('ai-chatbot-toggle');
    
    if (isOpen) {
      chatWindow.style.display = 'none';
      toggleButton.textContent = '💬';
    } else {
      chatWindow.style.display = 'flex';
      toggleButton.textContent = '✕';
    }
    
    isOpen = !isOpen;
  }
  
  // Minimize chat window
  function minimizeChat() {
    const chatWindow = document.getElementById('ai-chatbot-chat-window');
    const minimizeButton = document.getElementById('ai-chatbot-minimize');
    
    if (isMinimized) {
      chatWindow.style.height = '500px';
      minimizeButton.textContent = '−';
    } else {
      chatWindow.style.height = '60px';
      minimizeButton.textContent = '+';
    }
    
    isMinimized = !isMinimized;
  }
  
  // Add event listeners
  function addEventListeners() {
    const toggleButton = document.getElementById('ai-chatbot-toggle');
    const minimizeButton = document.getElementById('ai-chatbot-minimize');
    const sendButton = document.getElementById('ai-chatbot-send');
    const input = document.getElementById('ai-chatbot-input');
    
    toggleButton.addEventListener('click', toggleChat);
    minimizeButton.addEventListener('click', minimizeChat);
    sendButton.addEventListener('click', handleSend);
    
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        handleSend();
      }
    });
  }
  
  // Auto-open after delay
  function setupAutoOpen() {
    if (config.autoOpenDelay > 0) {
      setTimeout(() => {
        if (!isOpen) {
          toggleChat();
        }
      }, config.autoOpenDelay * 1000);
    }
  }
  
  // Initialize widget
  function init() {
    if (!botId) {
      console.error('AI Chatbot Widget: Bot ID not found');
      return;
    }
    
    createWidget();
    addEventListeners();
    setupAutoOpen();
  }
  
  // Start when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(); 