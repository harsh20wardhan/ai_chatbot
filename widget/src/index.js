import React from 'react';
import { createRoot } from 'react-dom/client';
import ChatWidget from './components/ChatWidget';
import { WidgetProvider } from './contexts/WidgetContext';

class AIChatbotWidget {
  constructor() {
    this.initialized = false;
    this.container = null;
    this.root = null;
    this.config = {
      botId: null,
      theme: 'light',
      primaryColor: '#3f51b5',
      position: 'bottom-right',
      welcomeMessage: null,
      placeholderText: null,
      showSources: true,
    };
  }

  init() {
    // Check if already initialized
    if (this.initialized) {
      console.warn('AI Chatbot Widget already initialized');
      return;
    }

    // Get bot ID from script tag data attribute
    const scriptTag = document.getElementById('ai-chatbot-widget');
    if (scriptTag) {
      this.config.botId = scriptTag.dataset.botId;
    }

    // If no bot ID found, check for a test bot ID
    if (!this.config.botId && process.env.NODE_ENV === 'development') {
      this.config.botId = 'test-bot-id';
    }

    // Create container element
    this.container = document.createElement('div');
    this.container.id = 'ai-chatbot-widget-container';
    document.body.appendChild(this.container);

    // Render React component
    this.root = createRoot(this.container);
    this.renderWidget();

    this.initialized = true;
    console.log('AI Chatbot Widget initialized with bot ID:', this.config.botId);
  }

  renderWidget() {
    this.root.render(
      <React.StrictMode>
        <WidgetProvider initialConfig={this.config}>
          <ChatWidget />
        </WidgetProvider>
      </React.StrictMode>
    );
  }

  updateConfig(newConfig) {
    this.config = {
      ...this.config,
      ...newConfig,
    };

    if (this.initialized) {
      this.renderWidget();
    }
  }

  destroy() {
    if (this.initialized && this.container) {
      this.root.unmount();
      document.body.removeChild(this.container);
      this.initialized = false;
      this.container = null;
      this.root = null;
    }
  }
}

// Initialize widget when script is loaded
const widget = new AIChatbotWidget();

// Initialize on DOM content loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => widget.init());
} else {
  widget.init();
}

export default widget;