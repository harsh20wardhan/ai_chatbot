import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// Start a website crawl
export const startCrawl = async ({ request, user, env, corsHeaders }) => {
  try {
    console.log('[CRAWL] Starting crawl request...');
    const { url, maxDepth, excludePatterns, botId } = await request.json();
    console.log('[CRAWL] Request data:', { url, maxDepth, excludePatterns, botId });
    
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
    console.log('[CRAWL] Verifying bot ownership for botId:', botId, 'userId:', user.id);
    
    // Verify bot ownership
    const { data: bot, error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();
      
    if (botError) {
      console.log('[CRAWL] Bot verification failed:', botError);
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log('[CRAWL] Bot verified successfully');
    
    // Create a crawl job
    console.log('[CRAWL] Creating crawl job in database...');
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
      console.log('[CRAWL] Failed to create crawl job:', jobError);
      return new Response(JSON.stringify({ error: jobError.message }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    console.log('[CRAWL] Crawl job created successfully:', job.id);

    // Trigger the crawler microservice (outside of Cloudflare Worker)
    // Since we can't run the Python crawler directly in the worker,
    // we need to notify our embedding/crawler microservice
    console.log('[CRAWL] Calling crawler service at:', env.CRAWLER_SERVICE_URL);
    try {
      const response = await fetch(`${env.CRAWLER_SERVICE_URL}/crawl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.CRAWLER_SERVICE_KEY}`
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
        console.log('[CRAWL] Crawler service returned error:', response.status, await response.text());
        // Update job status to failed
        await supabase
          .from('crawl_jobs')
          .update({ status: 'failed', error: 'Failed to start crawler service' })
          .eq('id', job.id);
          
        return new Response(JSON.stringify({ 
          error: 'Failed to start crawler service',
          job_id: job.id
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
      
      console.log('[CRAWL] Crawler service started successfully');
    } catch (serviceError) {
      console.log('[CRAWL] Crawler service error:', serviceError);
      // Update job status to failed
      await supabase
        .from('crawl_jobs')
        .update({ status: 'failed', error: 'Crawler service unavailable' })
        .eq('id', job.id);
        
      return new Response(JSON.stringify({ 
        error: 'Crawler service unavailable',
        job_id: job.id
      }), {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({ 
      message: 'Crawl job started successfully',
      job_id: job.id
    }), {
      status: 202, // Accepted
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to process crawl request' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get the status of a crawl job
export const getCrawlStatus = async ({ params, user, env, corsHeaders }) => {
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

// Delete/cancel a crawl job
export const deleteCrawlJob = async ({ params, user, env, corsHeaders }) => {
  try {
    const { jobId } = params;
    
    const supabase = getSupabase(env);
    
    // Check if the job exists and belongs to the user
    const { data, error: checkError } = await supabase
      .from('crawl_jobs')
      .select('id, status')
      .eq('id', jobId)
      .eq('user_id', user.id)
      .single();
      
    if (checkError) {
      return new Response(JSON.stringify({ error: 'Crawl job not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // If job is in-progress, try to cancel it
    if (data.status === 'in_progress') {
      try {
        const response = await fetch(`${env.CRAWLER_SERVICE_URL}/crawl/${jobId}/cancel`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${env.CRAWLER_SERVICE_KEY}`
          }
        });
        
        if (!response.ok) {
          console.error('Failed to cancel crawler job:', await response.text());
        }
      } catch (serviceError) {
        console.error('Crawler service unavailable for cancellation:', serviceError);
      }
    }
    
    // Update job status to cancelled
    const { error: updateError } = await supabase
      .from('crawl_jobs')
      .update({ status: 'cancelled' })
      .eq('id', jobId)
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
    
    return new Response(JSON.stringify({ message: 'Crawl job cancelled' }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to cancel crawl job' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get all crawl jobs for a specific bot
export const getCrawlJobsByBot = async ({ request, user, env, corsHeaders }) => {
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
    
    // Verify bot ownership and get crawl jobs
    const { data: crawlJobs, error } = await supabase
      .from('crawl_jobs')
      .select('*')
      .eq('bot_id', botId)
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
      
    if (error) {
      console.log('[CRAWL] Error fetching crawl jobs:', error);
      return new Response(JSON.stringify({ error: 'Failed to fetch crawl jobs' }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }

    return new Response(JSON.stringify({ 
      jobs: crawlJobs || []
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    console.error('[CRAWL] Error in getCrawlJobsByBot:', error);
    return new Response(JSON.stringify({ error: 'Failed to fetch crawl jobs' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 