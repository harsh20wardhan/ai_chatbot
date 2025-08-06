/**
 * AI Chatbot Widget Embed Script
 * 
 * This script creates a lightweight loader that injects the chatbot widget into any website.
 * It's designed to be as small as possible for fast loading.
 */

(function(window, document) {
  // Configuration
  const config = {
    scriptId: 'ai-chatbot-widget',
    containerId: 'ai-chatbot-widget-container',
    scriptSrc: 'https://your-domain.com/widget/ai-chatbot-widget.js', // Replace with actual URL
    defaultBotId: null // Will be replaced with the bot ID from the data attribute
  };
  
  // Check if script is already loaded
  if (document.getElementById(config.scriptId)) {
    console.warn('AI Chatbot Widget is already loaded');
    return;
  }
  
  // Get the current script tag
  const currentScript = document.currentScript;
  
  // Extract bot ID from data attribute
  if (currentScript) {
    config.defaultBotId = currentScript.dataset.botId;
  }
  
  // If no bot ID is provided, log an error and exit
  if (!config.defaultBotId) {
    console.error('AI Chatbot Widget: No bot ID provided. Add data-bot-id attribute to the script tag.');
    return;
  }
  
  // Create and append the script element
  const script = document.createElement('script');
  script.id = config.scriptId;
  script.src = config.scriptSrc;
  script.async = true;
  script.dataset.botId = config.defaultBotId;
  
  // Append script to document
  document.body.appendChild(script);
  
  // Create global object for widget
  window.AIChatbotWidget = window.AIChatbotWidget || {
    botId: config.defaultBotId,
    config: {},
    
    // Method to update widget configuration
    updateConfig: function(newConfig) {
      this.config = {
        ...this.config,
        ...newConfig
      };
      
      // Dispatch custom event that the widget will listen for
      const event = new CustomEvent('aichatbot:configUpdate', {
        detail: this.config
      });
      
      document.dispatchEvent(event);
    }
  };
  
})(window, document);