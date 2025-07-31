import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// Process a chat message using RAG
export const processChat = async ({ request, env, corsHeaders }) => {
  console.log('[CHAT] Request received');
  try {
    const data = await request.json();
    const { query, botId, bot_id, conversationId, messageHistory = [] } = data;
    console.log(`[CHAT] Request data: query="${query?.substring(0, 30)}...", botId=${botId || bot_id}, conversationId=${conversationId}`);
    
    // Accept either botId or bot_id parameter
    const actualBotId = botId || bot_id;
    
    if (!query) {
      console.log('[CHAT] Error: Query is required');
      return new Response(JSON.stringify({ error: 'Query is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    if (!actualBotId) {
      console.log('[CHAT] Error: Bot ID is required');
      return new Response(JSON.stringify({ error: 'Bot ID is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log(`[CHAT] Initializing Supabase with URL: ${env.SUPABASE_URL}`);
    const supabase = getSupabase(env);
    
    // Verify the bot exists
    console.log(`[CHAT] Checking if bot exists: ${actualBotId}`);
    const { data: bot, error: botError } = await supabase
      .from('bots')
      .select('id, name, settings')
      .eq('id', actualBotId)
      .single();
      
    if (botError) {
      console.log(`[CHAT] Bot not found: ${botError.message}`);
      return new Response(JSON.stringify({ error: 'Bot not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log(`[CHAT] Bot found: ${bot.name}`);
    
    // Create or get conversation
    let conversation;
    if (conversationId) {
      console.log(`[CHAT] Getting existing conversation: ${conversationId}`);
      const { data, error } = await supabase
        .from('conversations')
        .select('*')
        .eq('id', conversationId)
        .eq('bot_id', actualBotId)
        .single();
        
      if (error) {
        console.log(`[CHAT] Creating new conversation, existing not found: ${error.message}`);
        // If conversation not found, create a new one
        const { data: newConversation, error: createError } = await supabase
          .from('conversations')
          .insert([{
            bot_id: actualBotId,
            created_at: new Date().toISOString(),
            title: query.substring(0, 50) + (query.length > 50 ? '...' : '')
          }])
          .select()
          .single();
          
        if (createError) {
          console.log(`[CHAT] Failed to create conversation: ${createError.message}`);
          return new Response(JSON.stringify({ error: 'Failed to create conversation' }), {
            status: 500,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders
            }
          });
        }
        
        conversation = newConversation;
        console.log(`[CHAT] New conversation created: ${conversation.id}`);
      } else {
        conversation = data;
        console.log(`[CHAT] Using existing conversation: ${conversation.id}`);
      }
    } else {
      // Create a new conversation
      console.log(`[CHAT] No conversation ID provided, creating new conversation`);
      const { data: newConversation, error: createError } = await supabase
        .from('conversations')
        .insert([{
          bot_id: actualBotId,
          created_at: new Date().toISOString(),
          title: query.substring(0, 50) + (query.length > 50 ? '...' : '')
        }])
        .select()
        .single();
        
      if (createError) {
        console.log(`[CHAT] Failed to create conversation: ${createError.message}`);
        return new Response(JSON.stringify({ error: 'Failed to create conversation' }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
      
      conversation = newConversation;
      console.log(`[CHAT] New conversation created: ${conversation.id}`);
    }
    
    // Store user message in database
    console.log(`[CHAT] Storing user message in database`);
    const { error: messageError } = await supabase
      .from('messages')
      .insert([{
        conversation_id: conversation.id,
        role: 'user',
        content: query,
        created_at: new Date().toISOString()
      }]);
      
    if (messageError) {
      console.error(`[CHAT] Failed to store user message: ${messageError.message}`);
      // Continue anyway
    } else {
      console.log(`[CHAT] User message stored successfully`);
    }
    
    // Call the RAG microservice
    console.log(`[CHAT] Calling RAG service at ${env.RAG_SERVICE_URL}/chat`);
    try {
      const ragPayload = {
        query,
        bot_id: actualBotId,
        conversation_id: conversation.id,
        message_history: messageHistory
      };
      console.log(`[CHAT] RAG payload: ${JSON.stringify(ragPayload)}`);
      
      const response = await fetch(`${env.RAG_SERVICE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.RAG_SERVICE_KEY}`
        },
        body: JSON.stringify(ragPayload)
      });
      
      console.log(`[CHAT] RAG service response status: ${response.status}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`[CHAT] RAG service error: ${errorText}`);
        
        return new Response(JSON.stringify({ 
          error: 'Failed to process query',
          conversation_id: conversation.id 
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
      
      console.log(`[CHAT] Parsing RAG service response`);
      const ragResponse = await response.json();
      console.log(`[CHAT] Answer received (first 50 chars): ${ragResponse.answer.substring(0, 50)}...`);
      
      // Store assistant's response in database
      console.log(`[CHAT] Storing assistant message in database`);
      const { error: assistantMessageError } = await supabase
        .from('messages')
        .insert([{
          conversation_id: conversation.id,
          role: 'assistant',
          content: ragResponse.answer,
          metadata: {
            sources: ragResponse.sources,
            tokens_used: ragResponse.tokens_used
          },
          created_at: new Date().toISOString()
        }]);
        
      if (assistantMessageError) {
        console.error(`[CHAT] Failed to store assistant message: ${assistantMessageError.message}`);
        // Continue anyway
      } else {
        console.log(`[CHAT] Assistant message stored successfully`);
      }
      
      console.log(`[CHAT] Sending successful response to client`);
      return new Response(JSON.stringify({
        answer: ragResponse.answer,
        sources: ragResponse.sources,
        conversation_id: conversation.id
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (serviceError) {
      console.error(`[CHAT] RAG service error: ${serviceError.message}`);
      console.error(`[CHAT] Error stack: ${serviceError.stack}`);
      
      return new Response(JSON.stringify({ 
        error: 'RAG service unavailable',
        conversation_id: conversation.id 
      }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  } catch (error) {
    console.error(`[CHAT] Error processing chat: ${error.message}`);
    console.error(`[CHAT] Error stack: ${error.stack}`);
    
    return new Response(JSON.stringify({ error: 'Failed to process chat request' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get all conversations for a bot
export const getConversations = async ({ request, user, env, corsHeaders }) => {
  try {
    const url = new URL(request.url);
    const botId = url.searchParams.get('botId');
    
    if (!botId) {
      return new Response(JSON.stringify({ error: 'Bot ID is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    const supabase = getSupabase(env);
    
    // Verify bot ownership
    const { error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Get conversations for the bot
    const { data, error } = await supabase
      .from('conversations')
      .select('id, title, created_at, updated_at')
      .eq('bot_id', botId)
      .order('updated_at', { ascending: false });
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ conversations: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve conversations' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get a conversation with its messages
export const getConversation = async ({ params, user, env, corsHeaders }) => {
  try {
    const { conversationId } = params;
    
    const supabase = getSupabase(env);
    
    // Get conversation details
    const { data: conversation, error: convError } = await supabase
      .from('conversations')
      .select('*, bots(id, user_id)')
      .eq('id', conversationId)
      .single();
      
    if (convError) {
      return new Response(JSON.stringify({ error: 'Conversation not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Verify bot ownership
    if (conversation.bots.user_id !== user.id) {
      return new Response(JSON.stringify({ error: 'Access denied' }), {
        status: 403,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Get messages for the conversation
    const { data: messages, error: messagesError } = await supabase
      .from('messages')
      .select('*')
      .eq('conversation_id', conversationId)
      .order('created_at', { ascending: true });
      
    if (messagesError) {
      return new Response(JSON.stringify({ error: messagesError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Remove the bots join data
    const { bots, ...conversationData } = conversation;
    
    return new Response(JSON.stringify({ 
      conversation: conversationData,
      messages 
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve conversation' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 