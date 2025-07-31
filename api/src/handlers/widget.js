import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_KEY);
};

// Get widget configuration
export const getWidgetConfig = async ({ params, env, corsHeaders }) => {
  try {
    const { botId } = params;
    
    const supabase = getSupabase(env);
    
    // Get bot details
    const { data, error } = await supabase
      .from('bots')
      .select('id, name, settings')
      .eq('id', botId)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: 'Bot not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Extract widget-relevant settings
    const widgetConfig = {
      bot_id: data.id,
      name: data.name,
      theme: data.settings?.widget?.theme || 'light',
      primary_color: data.settings?.widget?.primary_color || '#007BFF',
      position: data.settings?.widget?.position || 'bottom-right',
      welcome_message: data.settings?.widget?.welcome_message || `Hi there! I'm ${data.name}. How can I help you today?`,
      placeholder_text: data.settings?.widget?.placeholder_text || 'Ask me anything...',
      show_sources: data.settings?.widget?.show_sources !== false // Default to true
    };
    
    return new Response(JSON.stringify({ config: widgetConfig }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve widget configuration' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Update widget configuration
export const updateWidgetConfig = async ({ request, params, user, env, corsHeaders }) => {
  try {
    const { botId } = params;
    const updates = await request.json();
    
    const supabase = getSupabase(env);
    
    // Verify bot ownership
    const { data: bot, error: botError } = await supabase
      .from('bots')
      .select('id, settings')
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
    
    // Validate widget configuration
    const validKeys = [
      'theme', 
      'primary_color', 
      'position', 
      'welcome_message', 
      'placeholder_text', 
      'show_sources'
    ];
    
    const invalidKeys = Object.keys(updates).filter(key => !validKeys.includes(key));
    
    if (invalidKeys.length > 0) {
      return new Response(JSON.stringify({ 
        error: `Invalid configuration keys: ${invalidKeys.join(', ')}`,
        valid_keys: validKeys
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Merge with existing settings
    const existingSettings = bot.settings || {};
    const existingWidgetSettings = existingSettings.widget || {};
    
    const updatedSettings = {
      ...existingSettings,
      widget: {
        ...existingWidgetSettings,
        ...updates
      }
    };
    
    // Update bot settings
    const { error: updateError } = await supabase
      .from('bots')
      .update({
        settings: updatedSettings,
        updated_at: new Date().toISOString()
      })
      .eq('id', botId)
      .eq('user_id', user.id);
      
    if (updateError) {
      return new Response(JSON.stringify({ error: updateError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Widget configuration updated successfully',
      config: updatedSettings.widget
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to update widget configuration' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 