import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// Start a realtime crawl
export const startRealtimeCrawl = async ({ request, user, env, corsHeaders }) => {
  // Fallback test user for unauthenticated testing
  if (!user) {
    user = { id: '00000000-0000-0000-0000-000000000000', email: 'test@example.com' };
  }
  try {
    console.log('[REALTIME_CRAWL] Starting realtime crawl request...');
    const { url, maxDepth, excludePatterns, botId } = await request.json();
    console.log('[REALTIME_CRAWL] Request data:', { url, maxDepth, excludePatterns, botId });
    
    if (!url) {
      return new Response(JSON.stringify({ error: 'URL is required' }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }

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
    console.log('[REALTIME_CRAWL] Verifying bot ownership for botId:', botId, 'userId:', user.id);
    
    // Verify bot ownership
    const { data: bot, error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      console.log('[REALTIME_CRAWL] Bot verification failed:', botError);
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log('[REALTIME_CRAWL] Bot verified successfully');
    
    // Create a crawl job
    console.log('[REALTIME_CRAWL] Creating crawl job in database...');
    const { data: job, error: jobError } = await supabase
      .from('crawl_jobs')
      .insert([
        {
          bot_id: botId,
          user_id: user.id,
          url,
          max_depth: maxDepth || 3,
          exclude_patterns: excludePatterns || [],
          status: 'pending',
          created_at: new Date().toISOString()
        }
      ])
      .select()
      .single();
      
    if (jobError) {
      console.log('[REALTIME_CRAWL] Failed to create crawl job:', jobError);
      return new Response(JSON.stringify({ error: jobError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log('[REALTIME_CRAWL] Crawl job created successfully:', job.id);

    // Call the realtime crawler service
    console.log('[REALTIME_CRAWL] Calling realtime crawler service at:', env.REALTIME_CRAWL_SERVICE_URL);
    try {
      const response = await fetch(`${env.REALTIME_CRAWL_SERVICE_URL}/realtime-crawl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.REALTIME_CRAWL_SERVICE_KEY}`
        },
        body: JSON.stringify({
          job_id: job.id,
          url,
          max_depth: maxDepth || 3,
          exclude_patterns: excludePatterns || [],
          bot_id: botId
        })
      });
      
      if (!response.ok) {
        console.log('[REALTIME_CRAWL] Realtime crawler service returned error:', response.status, await response.text());
        // Update job status to failed
        await supabase
          .from('crawl_jobs')
          .update({ status: 'failed', error: 'Failed to start realtime crawler service' })
          .eq('id', job.id);
          
        return new Response(JSON.stringify({ 
          error: 'Failed to start realtime crawler service',
          job_id: job.id
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
      
      const realtimeResponse = await response.json();
      console.log('[REALTIME_CRAWL] Realtime crawler service started successfully:', realtimeResponse);
      
      return new Response(JSON.stringify({ 
        message: 'Realtime crawl job started successfully',
        job_id: job.id,
        session_id: realtimeResponse.session_id,
        websocket_url: env.REALTIME_CRAWL_WEBSOCKET_URL || `${env.REALTIME_CRAWL_SERVICE_URL.replace('http', 'ws')}`
      }), {
        status: 202, // Accepted
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    } catch (serviceError) {
      console.log('[REALTIME_CRAWL] Realtime crawler service error:', serviceError);
      // Update job status to failed
      await supabase
        .from('crawl_jobs')
        .update({ status: 'failed', error: 'Realtime crawler service unavailable' })
        .eq('id', job.id);
        
      return new Response(JSON.stringify({ 
        error: 'Realtime crawler service unavailable',
        job_id: job.id
      }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  } catch (error) {
    console.error('[REALTIME_CRAWL] Error:', error);
    return new Response(JSON.stringify({ error: 'Failed to process realtime crawl request' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get realtime crawl status
export const getRealtimeCrawlStatus = async ({ params, user, env, corsHeaders }) => {
  try {
    const { jobId } = params;
    
    const supabase = getSupabase(env);
    const { data, error } = await supabase
      .from('crawl_jobs')
      .select('*')
      .eq('id', jobId)
      .eq('user_id', user.id)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: 'Crawl job not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Get detailed status from realtime crawler service
    try {
      const response = await fetch(`${env.REALTIME_CRAWL_SERVICE_URL}/crawl-status/${jobId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${env.REALTIME_CRAWL_SERVICE_KEY}`
        }
      });
      
      if (response.ok) {
        const detailedStatus = await response.json();
        return new Response(JSON.stringify({ 
          job: data,
          detailed_status: detailedStatus
        }), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
    } catch (serviceError) {
      console.log('[REALTIME_CRAWL] Error getting detailed status:', serviceError);
    }
    
    // Fallback to basic job data
    return new Response(JSON.stringify({ job: data }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get crawl status' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get crawled pages for a job
export const getCrawledPages = async ({ params, user, env, corsHeaders }) => {
  try {
    const { jobId } = params;
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const offset = (page - 1) * limit;
    
    const supabase = getSupabase(env);
    
    // Verify job ownership
    const { data: job, error: jobError } = await supabase
      .from('crawl_jobs')
      .select('id')
      .eq('id', jobId)
      .eq('user_id', user.id)
      .single();
      
    if (jobError) {
      return new Response(JSON.stringify({ error: 'Crawl job not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Get crawled pages
    const { data: pages, error: pagesError, count } = await supabase
      .from('crawled_pages')
      .select('id, url, title, content_length, status, created_at, embedded_at', { count: 'exact' })
      .eq('crawl_job_id', jobId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);
      
    if (pagesError) {
      return new Response(JSON.stringify({ error: pagesError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      pages,
      pagination: {
        page,
        limit,
        total: count,
        total_pages: Math.ceil(count / limit)
      }
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get crawled pages' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get page content
export const getPageContent = async ({ params, user, env, corsHeaders }) => {
  try {
    const { pageId } = params;
    
    const supabase = getSupabase(env);
    
    // Get page content with ownership verification
    const { data: page, error } = await supabase
      .from('crawled_pages')
      .select('id, url, title, content, content_length, status, created_at')
      .eq('id', pageId)
      .eq('user_id', user.id)
      .single();
      
    if (error) {
      return new Response(JSON.stringify({ error: 'Page not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ page }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to get page content' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Delete crawled page
export const deleteCrawledPage = async ({ params, user, env, corsHeaders }) => {
  try {
    const { pageId } = params;
    
    const supabase = getSupabase(env);
    
    // Verify page ownership
    const { data: page, error: pageError } = await supabase
      .from('crawled_pages')
      .select('id, bot_id')
      .eq('id', pageId)
      .eq('user_id', user.id)
      .single();
      
    if (pageError) {
      return new Response(JSON.stringify({ error: 'Page not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Delete from Qdrant first
    try {
      const response = await fetch(`${env.EMBEDDING_SERVICE_URL}/documents/${pageId}/delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.EMBEDDING_SERVICE_KEY}`
        },
        body: JSON.stringify({
          bot_id: page.bot_id
        })
      });
      
      if (!response.ok) {
        console.log('[REALTIME_CRAWL] Error deleting from Qdrant:', await response.text());
      }
    } catch (serviceError) {
      console.log('[REALTIME_CRAWL] Embedding service error:', serviceError);
    }
    
    // Delete from database
    const { error: deleteError } = await supabase
      .from('crawled_pages')
      .delete()
      .eq('id', pageId)
      .eq('user_id', user.id);
      
    if (deleteError) {
      return new Response(JSON.stringify({ error: deleteError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ message: 'Page deleted successfully' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to delete page' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 