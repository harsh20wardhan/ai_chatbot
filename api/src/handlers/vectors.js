import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
};

// Get all vector collections for a user
export const getCollections = async ({ user, env, corsHeaders }) => {
  try {
    const supabase = getSupabase(env);
    
    // Get bots for the user
    const { data: bots, error: botsError } = await supabase
      .from('bots')
      .select('id, name')
      .eq('user_id', user.id);
      
    if (botsError) {
      return new Response(JSON.stringify({ error: botsError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Each bot has its own collection in Qdrant
    // We'll check which ones exist in Qdrant
    const botIds = bots.map(bot => bot.id);
    
    try {
      // Call the Qdrant API to get collection details
      const response = await fetch(`${env.QDRANT_URL}/collections`, {
        headers: { 
          'Content-Type': 'application/json',
          'api-key': env.QDRANT_API_KEY
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get collections: ${await response.text()}`);
      }
      
      const { result } = await response.json();
      const existingCollections = result.collections.map(c => c.name);
      
      // For each bot, check if its collection exists
      const collections = [];
      for (const bot of bots) {
        const exists = existingCollections.includes(bot.id);
        
        collections.push({
          id: bot.id,
          name: bot.name,
          exists,
          collection_name: bot.id
        });
      }
      
      return new Response(JSON.stringify({ collections }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (qdrantError) {
      console.error('Qdrant API error:', qdrantError);
      
      // Return just the bot info without Qdrant status
      const collections = bots.map(bot => ({
        id: bot.id,
        name: bot.name,
        exists: null, // Unknown status
        collection_name: bot.id
      }));
      
      return new Response(JSON.stringify({ 
        collections,
        warning: 'Vector database service unavailable' 
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get collections' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Create a new vector collection
export const createCollection = async ({ request, user, env, corsHeaders }) => {
  try {
    const { botId } = await request.json();
    
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
    const { data: bot, error: botError } = await supabase
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
    
    try {
      // Create a collection in Qdrant
      const response = await fetch(`${env.QDRANT_URL}/collections/${botId}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'api-key': env.QDRANT_API_KEY
        },
        body: JSON.stringify({
          vectors: {
            size: 768, // Size for InstructorXL embeddings
            distance: 'Cosine'
          }
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        
        // If collection already exists, just return success
        if (errorData.status && errorData.status.error && errorData.status.error.includes('already exists')) {
          return new Response(JSON.stringify({ 
            message: 'Collection already exists',
            collection_name: botId
          }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders
            }
          });
        }
        
        throw new Error(`Failed to create collection: ${JSON.stringify(errorData)}`);
      }
      
      return new Response(JSON.stringify({ 
        message: 'Collection created successfully',
        collection_name: botId
      }), {
        status: 201,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (qdrantError) {
      console.error('Qdrant API error:', qdrantError);
      
      return new Response(JSON.stringify({ error: 'Vector database service unavailable' }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to create collection' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Delete a vector collection
export const deleteCollection = async ({ params, user, env, corsHeaders }) => {
  try {
    const { collectionId } = params;
    
    const supabase = getSupabase(env);
    
    // Verify bot ownership (bot ID is used as collection name)
    const { data: bot, error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', collectionId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      return new Response(JSON.stringify({ error: 'Collection not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    try {
      // Delete the collection from Qdrant
      const response = await fetch(`${env.QDRANT_URL}/collections/${collectionId}`, {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          'api-key': env.QDRANT_API_KEY
        }
      });
      
      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Failed to delete collection: ${errorData}`);
      }
      
      // Reset the status of all embedded documents back to processed
      await supabase
        .from('documents')
        .update({ status: 'processed' })
        .eq('bot_id', collectionId)
        .eq('status', 'embedded');
      
      return new Response(JSON.stringify({ message: 'Collection deleted successfully' }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (qdrantError) {
      console.error('Qdrant API error:', qdrantError);
      
      return new Response(JSON.stringify({ error: 'Vector database service unavailable' }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to delete collection' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 