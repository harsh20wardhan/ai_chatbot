import { createClient } from '@supabase/supabase-js';

// Helper to initialize Supabase client
const getSupabase = (env) => {
  return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);
};

// Get admin stats
export const getStats = async ({ user, env, corsHeaders }) => {
  try {
    const supabase = getSupabase(env);
    
    // Get counts of bots, documents, and conversations
    const [
      { count: botCount, error: botError },
      { count: documentCount, error: docError },
      { count: conversationCount, error: convError },
      { count: messageCount, error: msgError }
    ] = await Promise.all([
      supabase.from('bots').select('*', { count: 'exact', head: true }).eq('user_id', user.id),
      supabase.from('documents').select('*', { count: 'exact', head: true }).eq('user_id', user.id),
      supabase.from('conversations').select('*', { count: 'exact', head: true }).in('bot_id', supabase.from('bots').select('id').eq('user_id', user.id)),
      supabase.from('messages').select('*', { count: 'exact', head: true }).in('conversation_id', supabase.from('conversations').select('id').in('bot_id', supabase.from('bots').select('id').eq('user_id', user.id)))
    ]);
    
    if (botError || docError || convError || msgError) {
      return new Response(JSON.stringify({ error: 'Failed to retrieve statistics' }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Get recent activity
    const { data: recentActivity, error: activityError } = await supabase
      .from('messages')
      .select('created_at, role, conversation_id, conversations:conversation_id(bot_id, bots:bot_id(name))')
      .in('conversations.bot_id', supabase.from('bots').select('id').eq('user_id', user.id))
      .order('created_at', { ascending: false })
      .limit(10);
      
    if (activityError) {
      console.error('Failed to get recent activity:', activityError);
      // Continue with other stats
    }
    
    // Get jobs status
    const [
      { data: crawlJobs, error: crawlJobsError },
      { data: embeddingJobs, error: embeddingJobsError }
    ] = await Promise.all([
      supabase.from('crawl_jobs').select('*').eq('user_id', user.id).order('created_at', { ascending: false }).limit(5),
      supabase.from('embedding_jobs').select('*').eq('user_id', user.id).order('created_at', { ascending: false }).limit(5)
    ]);
    
    if (crawlJobsError || embeddingJobsError) {
      console.error('Failed to get jobs:', crawlJobsError || embeddingJobsError);
      // Continue with other stats
    }
    
    return new Response(JSON.stringify({
      stats: {
        bot_count: botCount,
        document_count: documentCount,
        conversation_count: conversationCount,
        message_count: messageCount
      },
      recent_activity: recentActivity || [],
      recent_jobs: {
        crawl_jobs: crawlJobs || [],
        embedding_jobs: embeddingJobs || []
      }
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve admin statistics' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get logs
export const getLogs = async ({ request, user, env, corsHeaders }) => {
  try {
    const url = new URL(request.url);
    const type = url.searchParams.get('type') || 'all';
    const limit = parseInt(url.searchParams.get('limit') || '50', 10);
    
    const supabase = getSupabase(env);
    let logs = [];
    
    if (type === 'all' || type === 'crawl') {
      // Get crawl logs
      const { data: crawlLogs, error: crawlError } = await supabase
        .from('crawl_jobs')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(limit);
        
      if (crawlError) {
        console.error('Failed to get crawl logs:', crawlError);
      } else {
        logs = [...logs, ...crawlLogs.map(log => ({ ...log, type: 'crawl' }))];
      }
    }
    
    if (type === 'all' || type === 'embedding') {
      // Get embedding logs
      const { data: embeddingLogs, error: embeddingError } = await supabase
        .from('embedding_jobs')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(limit);
        
      if (embeddingError) {
        console.error('Failed to get embedding logs:', embeddingError);
      } else {
        logs = [...logs, ...embeddingLogs.map(log => ({ ...log, type: 'embedding' }))];
      }
    }
    
    if (type === 'all' || type === 'chat') {
      // Get chat logs (messages)
      const { data: chatLogs, error: chatError } = await supabase
        .from('messages')
        .select('*, conversations:conversation_id(bot_id, title)')
        .in('conversations.bot_id', supabase.from('bots').select('id').eq('user_id', user.id))
        .order('created_at', { ascending: false })
        .limit(limit);
        
      if (chatError) {
        console.error('Failed to get chat logs:', chatError);
      } else {
        logs = [...logs, ...chatLogs.map(log => ({ ...log, type: 'chat' }))];
      }
    }
    
    // Sort all logs by creation date
    logs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Limit to the requested number
    logs = logs.slice(0, limit);
    
    return new Response(JSON.stringify({
      logs,
      count: logs.length
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve logs' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
};

// Get active jobs
export const getJobs = async ({ user, env, corsHeaders }) => {
  try {
    const supabase = getSupabase(env);
    
    // Get active jobs (in_progress or pending)
    const [
      { data: crawlJobs, error: crawlJobsError },
      { data: embeddingJobs, error: embeddingJobsError }
    ] = await Promise.all([
      supabase
        .from('crawl_jobs')
        .select('*')
        .eq('user_id', user.id)
        .in('status', ['pending', 'in_progress'])
        .order('created_at', { ascending: false }),
      supabase
        .from('embedding_jobs')
        .select('*')
        .eq('user_id', user.id)
        .in('status', ['pending', 'in_progress'])
        .order('created_at', { ascending: false })
    ]);
    
    if (crawlJobsError || embeddingJobsError) {
      console.error('Failed to get jobs:', crawlJobsError || embeddingJobsError);
      return new Response(JSON.stringify({ error: 'Failed to retrieve active jobs' }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    return new Response(JSON.stringify({
      crawl_jobs: crawlJobs || [],
      embedding_jobs: embeddingJobs || [],
      active_job_count: (crawlJobs?.length || 0) + (embeddingJobs?.length || 0)
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to retrieve active jobs' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
}; 