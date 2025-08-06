# AI Chatbot Widget Demo Website

This is a demo website to test the embedded AI chatbot widget functionality with RAG (Retrieval-Augmented Generation) capabilities.

## 🚀 Quick Start

### Prerequisites
Make sure you have the following services running:

1. **Dashboard** (React app): `http://localhost:3000`
2. **API Gateway**: `http://localhost:8787`
3. **RAG Service**: `http://localhost:8004`
4. **Qdrant Vector DB**: `http://localhost:6333`
5. **Realtime Crawl Service**: `http://localhost:8005`
6. **Parser Service**: `http://localhost:8006`
7. **Embedding Service**: `http://localhost:8007`

### Running the Demo Website

1. **Start the demo server**:
   ```bash
   cd demo-website
   node server.js
   ```

2. **Open the demo website**:
   ```
   http://localhost:8080
   ```

3. **Test the widget**:
   - Look for the chat button (💬) in the bottom-right corner
   - Click it to open the AI assistant
   - Ask questions about your uploaded documents or crawled websites
   - See source attribution for each answer

## 📋 What's Included

### Files
- `index.html` - The demo website with embedded widget
- `server.js` - Simple HTTP server to serve the demo
- `README.md` - This file

### Widget Features
- ✅ **RAG-enabled chat** - Uses your documents and crawled websites
- ✅ **Source attribution** - Shows which documents were used (3-word preview)
- ✅ **Responsive design** - Works on all devices
- ✅ **Customizable** - Colors, position, theme
- ✅ **Minimize/maximize** - Collapsible chat window
- ✅ **Real-time chat** - Instant message sending and receiving
- ✅ **Error handling** - Graceful error messages
- ✅ **Conversation tracking** - Maintains conversation context

## 🔧 Widget Configuration

The widget is configured with:
- **Position**: Bottom-right corner
- **Theme**: Light mode
- **Primary Color**: #3f51b5 (Material UI Blue)
- **Bot ID**: `6a582832-e37c-43d2-b2e1-eaac0d4fad19`
- **API Endpoint**: `http://localhost:8787/api/chat`

## 📝 Embed Code

The demo uses this embed code:

```html
<script>
  (function(w, d, s, o) {
    w.AIChatWidget = o;
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(o)) return;
    js = d.createElement(s); js.id = o;
    js.src = 'http://localhost:3000/widget/ai-chatbot-widget.js';
    js.async = 1;
    js.dataset.botId = '6a582832-e37c-43d2-b2e1-eaac0d4fad19';
    fjs.parentNode.insertBefore(js, fjs);
  }(window, document, 'script', 'ai-chatbot-widget'));
</script>
```

### For Production Use
Replace `http://localhost:3000` with your actual dashboard domain:
```html
js.src = 'https://your-domain.com/widget/ai-chatbot-widget.js';
```

## 🧪 Testing Scenarios

1. **Basic Chat**: Ask general questions to test the AI
2. **Document Questions**: Ask about content from uploaded documents
3. **Website Questions**: Ask about content from crawled websites
4. **Source Attribution**: Check that sources are displayed correctly (3-word preview)
5. **Mobile Testing**: Test on different screen sizes
6. **Error Handling**: Test with network issues or API errors

## 🔄 Complete Workflow

### 1. **Setup Bot and Data**
1. Go to dashboard: `http://localhost:3000`
2. Create a new bot or use existing one
3. Upload documents (PDF, DOCX, TXT, Excel)
4. Crawl websites for additional context
5. Wait for embedding and processing to complete

### 2. **Configure Widget**
1. Navigate to bot's widget configuration
2. Customize colors, theme, position
3. Set welcome message and placeholder text
4. Save configuration

### 3. **Test on Demo Website**
1. Start demo server: `node server.js`
2. Open `http://localhost:8080`
3. Test chat functionality
4. Verify source attribution

### 4. **Embed on Your Website**
1. Copy the embed code from widget configuration
2. Paste into your website's HTML
3. Replace localhost URLs with production URLs
4. Test on your live website

## 🐛 Troubleshooting

### Widget not appearing?
- Check that the dashboard is running on `localhost:3000`
- Check browser console for JavaScript errors
- Verify the widget script is accessible at `/widget/ai-chatbot-widget.js`
- Ensure the bot ID in the embed code is correct

### Chat not working?
- Check that the API is running on `localhost:8787`
- Check that the RAG service is running on `localhost:8004`
- Check browser network tab for API errors
- Verify the API URL in the widget script is correct

### Sources not showing?
- Check that documents have been uploaded and embedded
- Check that websites have been crawled and embedded
- Verify the Qdrant vector database is running
- Check that the RAG service is processing requests correctly

### 404 API Errors?
- Ensure all microservices are running
- Check API gateway routing configuration
- Verify CORS settings in API gateway
- Check that the widget is using the correct API URL

## 📱 Mobile Testing

The widget is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Tablet browsers (iPad, Android tablets)
- Mobile browsers (iPhone, Android phones)
- Different screen orientations

## 🎨 Customization

You can customize the widget by:
1. Going to your dashboard: `http://localhost:3000`
2. Navigate to a bot's widget configuration
3. Modify colors, theme, position, and messages
4. Save the configuration
5. Refresh the demo website to see changes

### Available Customizations:
- **Primary Color**: Change the main brand color
- **Theme**: Light or dark mode
- **Position**: Bottom-right or bottom-left
- **Welcome Message**: Custom greeting text
- **Placeholder Text**: Input field placeholder
- **Show Sources**: Toggle source attribution

## 🔗 Related Links

- **Dashboard**: `http://localhost:3000`
- **API Gateway**: `http://localhost:8787`
- **Widget Preview**: `http://localhost:3000/widget-preview/6a582832-e37c-43d2-b2e1-eaac0d4fad19`
- **RAG Service**: `http://localhost:8004`
- **Qdrant Vector DB**: `http://localhost:6333`

## 🚀 Production Deployment

### For Production Use:
1. **Update API URLs**: Replace `localhost:8787` with your production API domain
2. **Update Widget URL**: Replace `localhost:3000` with your production dashboard domain
3. **Configure CORS**: Ensure your API gateway allows requests from your website domain
4. **SSL/HTTPS**: Use HTTPS for all production URLs
5. **Domain Configuration**: Update widget script to use your actual domain

### Example Production Embed Code:
```html
<script>
  (function(w, d, s, o) {
    w.AIChatWidget = o;
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(o)) return;
    js = d.createElement(s); js.id = o;
    js.src = 'https://your-dashboard.com/widget/ai-chatbot-widget.js';
    js.async = 1;
    js.dataset.botId = 'your-bot-id-here';
    fjs.parentNode.insertBefore(js, fjs);
  }(window, document, 'script', 'ai-chatbot-widget'));
</script>
```

## 📊 Performance Tips

- **Widget Loading**: The widget loads asynchronously to avoid blocking page load
- **API Caching**: Consider implementing response caching for better performance
- **CDN**: Host the widget script on a CDN for faster loading
- **Compression**: Enable gzip compression on your web server
- **Minification**: Minify the widget JavaScript for production

## 🔒 Security Considerations

- **CORS**: Configure proper CORS headers in your API gateway
- **Authentication**: Consider adding authentication for sensitive bots
- **Rate Limiting**: Implement rate limiting on chat endpoints
- **Input Validation**: Validate all user inputs on both client and server
- **HTTPS**: Always use HTTPS in production

## 🆘 Support

If you encounter issues:
1. Check the browser console for JavaScript errors
2. Check the network tab for failed API requests
3. Verify all services are running on correct ports
4. Check the API gateway logs for routing issues
5. Ensure your bot has uploaded documents or crawled websites 