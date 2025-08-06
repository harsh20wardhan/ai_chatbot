import { Router } from './router';
import { corsMiddleware } from './middleware/cors';
import { authMiddleware } from './middleware/auth';
import { createClient } from '@supabase/supabase-js';

// Import handlers
import * as authHandler from './handlers/auth';
import * as botsHandler from './handlers/bots';
import * as crawlHandler from './handlers/crawl';
import * as realtimeCrawlHandler from './handlers/realtime_crawl';
import * as documentsHandler from './handlers/documents';
import * as embeddingsHandler from './handlers/embeddings';
import * as vectorsHandler from './handlers/vectors';
import * as chatHandler from './handlers/chat';
import * as adminHandler from './handlers/admin';
import * as widgetHandler from './handlers/widget';

const router = new Router();

// Apply CORS middleware to all routes
router.use(corsMiddleware);

// Health check endpoint
router.get('/api/health', authHandler.healthCheck);

// Test endpoint for Supabase configuration
router.get('/api/test/supabase-config', async ({ env, corsHeaders }) => {
  try {
    const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY);
    
    // Try to get the current user (this will fail, but we can see the error)
    const { data, error } = await supabase.auth.getUser();
    
    return new Response(JSON.stringify({ 
      message: 'Supabase configuration test',
      hasUrl: !!env.SUPABASE_URL,
      hasAnonKey: !!env.SUPABASE_ANON_KEY,
      hasServiceKey: !!env.SUPABASE_SERVICE_ROLE_KEY,
      error: error ? error.message : null,
      data: data ? 'User data available' : 'No user data'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      error: 'Failed to test Supabase configuration',
      details: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// Test endpoint for debugging (remove in production)
router.post('/api/test/bot', async ({ request, env, corsHeaders }) => {
  try {
    const { name, description, website_url } = await request.json();
    
    if (!name) {
      return new Response(JSON.stringify({ error: 'Bot name is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    // Use a fixed test user ID for debugging
    const testUserId = '00000000-0000-0000-0000-000000000000';
    
    // Initialize Supabase
    const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
    
    console.log("Creating bot with test user ID:", testUserId);
    console.log("Bot details:", { name, description, website_url });
    
    // Insert the bot
    const { data, error } = await supabase
      .from('bots')
      .insert([{
        name,
        description,
        website_url,
        user_id: testUserId,
        created_at: new Date().toISOString()
      }])
      .select()
      .single();
      
    if (error) {
      console.error("Supabase error:", error);
      return new Response(JSON.stringify({ error: error.message, details: error }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
    
    console.log("Bot created successfully:", data);
    
    // Create Qdrant collection
    try {
      console.log(`Creating Qdrant collection at ${env.QDRANT_URL}/collections/${data.id}`);
      const response = await fetch(`${env.QDRANT_URL}/collections/${data.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'api-key': env.QDRANT_API_KEY || ''
        },
        body: JSON.stringify({
          vectors: {
            size: 768,
            distance: 'Cosine'
          }
        })
      });
      
      if (!response.ok) {
        console.error(`Qdrant error: ${response.status} ${response.statusText}`);
        const errorText = await response.text();
        console.error(`Qdrant error details: ${errorText}`);
      }
    } catch (qdrantError) {
      console.error("Qdrant connection error:", qdrantError);
    }
    
    return new Response(JSON.stringify({ 
      message: 'Test bot created successfully', 
      bot: data 
    }), {
      status: 201,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    console.error("Test endpoint error:", error);
    return new Response(JSON.stringify({ 
      error: 'Failed to create test bot', 
      details: error.message,
      stack: error.stack 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});

// Auth routes
router.post('/api/auth/register', authHandler.register);
router.post('/api/auth/login', authHandler.login);
router.post('/api/auth/logout', authHandler.logout);
router.get('/api/auth/user', authMiddleware, authHandler.getUser);

// Bot management routes
router.get('/api/bots', authMiddleware, botsHandler.getBots);
router.post('/api/bots', authMiddleware, botsHandler.createBot);
router.get('/api/bots/:botId', authMiddleware, botsHandler.getBot);
router.put('/api/bots/:botId', authMiddleware, botsHandler.updateBot);
router.delete('/api/bots/:botId', authMiddleware, botsHandler.deleteBot);

// Crawler routes
router.post('/api/crawl/website', authMiddleware, crawlHandler.startCrawl);
router.get('/api/crawl/status/:jobId', authMiddleware, crawlHandler.getCrawlStatus);
router.get('/api/crawl/jobs', authMiddleware, crawlHandler.getCrawlJobsByBot);
router.delete('/api/crawl/job/:jobId', authMiddleware, crawlHandler.deleteCrawlJob);

// Realtime crawler routes
router.post('/api/realtime-crawl/start', authMiddleware, realtimeCrawlHandler.startRealtimeCrawl);
router.get('/api/realtime-crawl/status/:jobId', authMiddleware, realtimeCrawlHandler.getRealtimeCrawlStatus);
router.get('/api/realtime-crawl/jobs', authMiddleware, realtimeCrawlHandler.getRealtimeCrawlJobsByBot);
router.get('/api/realtime-crawl/pages/:jobId', authMiddleware, realtimeCrawlHandler.getCrawledPages);
router.get('/api/realtime-crawl/page/:pageId/content', authMiddleware, realtimeCrawlHandler.getPageContent);
router.delete('/api/realtime-crawl/page/:pageId', authMiddleware, realtimeCrawlHandler.deleteCrawledPage);

// Document parser routes
router.post('/api/documents/upload', authMiddleware, documentsHandler.uploadDocument);
router.get('/api/documents', authMiddleware, documentsHandler.getDocuments);
router.get('/api/documents/:documentId', authMiddleware, documentsHandler.getDocument);
router.delete('/api/documents/:documentId', authMiddleware, documentsHandler.deleteDocument);

// Embedding service routes
router.post('/api/embeddings/generate', authMiddleware, embeddingsHandler.generateEmbeddings);
router.get('/api/embeddings/status/:jobId', authMiddleware, embeddingsHandler.getEmbeddingStatus);
router.delete('/api/embeddings/delete/:botId', authMiddleware, embeddingsHandler.deleteEmbeddings);

// Vector DB routes
router.get('/api/vectors/collections', authMiddleware, vectorsHandler.getCollections);
router.post('/api/vectors/collections', authMiddleware, vectorsHandler.createCollection);
router.delete('/api/vectors/collections/:collectionId', authMiddleware, vectorsHandler.deleteCollection);

// RAG chat routes
router.post('/api/chat', chatHandler.processChat);
router.get('/api/chat/conversations', authMiddleware, chatHandler.getConversations);
router.get('/api/chat/conversations/:conversationId', authMiddleware, chatHandler.getConversation);

// Admin routes
router.get('/api/admin/stats', authMiddleware, adminHandler.getStats);
router.get('/api/admin/logs', authMiddleware, adminHandler.getLogs);
router.get('/api/admin/jobs', authMiddleware, adminHandler.getJobs);

// Widget routes
router.get('/api/widget/:botId/config', widgetHandler.getWidgetConfig);
router.post('/api/widget/:botId/config', authMiddleware, widgetHandler.updateWidgetConfig);

// Export the fetch handler for Cloudflare Workers
export default {
  async fetch(request, env, ctx) {
    return router.handle(request, env, ctx);
  }
}; 