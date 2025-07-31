import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// Get all bots for a user
export const getBots = async ({ user, env, corsHeaders }) => {
  try {
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('bots')
      .select('*')
      .eq('user_id', user.id);
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ bots: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve bots' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get a specific bot
export const getBot = async ({ params, user, env, corsHeaders }) => {
  try {
    const { botId } = params;
    
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('bots')
      .select('*')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: error.code === 'PGRST116' ? 404 : 400, // PGRST116 is "No rows returned"
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ bot: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve bot' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Create a new bot
export const createBot = async ({ request, user, env, corsHeaders }) => {
  try {
    const { name, description, website_url } = await request.json();
    
    if (!name) {
      return new Response(JSON.stringify({ error: 'Bot name is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('bots')
      .insert([
        {
          name,
          description,
          website_url,
          user_id: user.id,
          created_at: new Date().toISOString()
        }
      ])
      .select()
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Create a collection in Qdrant for this bot
    try {
      console.log(`Creating Qdrant collection for bot ${data.id} at ${env.QDRANT_URL}/collections/${data.id}`);
      
      const response = await fetch(`${env.QDRANT_URL}/collections/${data.id}`, {
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
        // Log error but don't fail the request
        console.error(`Failed to create Qdrant collection: ${response.status} ${response.statusText}`);
        const errorText = await response.text();
        console.error(`Error details: ${errorText}`);
      } else {
        console.log(`Successfully created Qdrant collection for bot ${data.id}`);
      }
    } catch (qdrantError) {
      console.error('Qdrant connection error:', qdrantError.message);
      console.error('Qdrant error stack:', qdrantError.stack);
    }
    
    return new Response(JSON.stringify({ 
      message: 'Bot created successfully', 
      bot: data 
    }), {
      status: 201,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to create bot' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Update a bot
export const updateBot = async ({ request, params, user, env, corsHeaders }) => {
  try {
    const { botId } = params;
    const updates = await request.json();
    
    // Remove any fields that shouldn't be updated directly
    const { user_id, id, created_at, ...safeUpdates } = updates;
    
    const supabase = getSupabase(env);
    
    // Check if bot exists and belongs to user
    const { data: existingBot, error: checkError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (checkError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Update the bot
    const { data, error } = await supabase
      .from('bots')
      .update({
        ...safeUpdates,
        updated_at: new Date().toISOString()
      })
      .eq('id', botId)
      .eq('user_id', user.id)
      .select()
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Bot updated successfully', 
      bot: data 
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to update bot' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Delete a bot
export const deleteBot = async ({ params, user, env, corsHeaders }) => {
  try {
    const { botId } = params;
    
    const supabase = getSupabase(env);
    
    // Check if bot exists and belongs to user
    const { data: existingBot, error: checkError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (checkError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Delete the bot
    const { error } = await supabase
      .from('bots')
      .delete()
      .eq('id', botId)
      .eq('user_id', user.id);
      
    if (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Delete the collection in Qdrant
    try {
      const response = await fetch(`${env.QDRANT_URL}/collections/${botId}`, {
        method: 'DELETE',
        headers: { 
          'Content-Type': 'application/json',
          'api-key': env.QDRANT_API_KEY
        }
      });
      
      if (!response.ok) {
        // Log error but don't fail the request
        console.error('Failed to delete Qdrant collection:', await response.text());
      }
    } catch (qdrantError) {
      console.error('Qdrant connection error:', qdrantError);
    }
    
    return new Response(JSON.stringify({ message: 'Bot deleted successfully' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to delete bot' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 