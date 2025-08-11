import { createClient } from '@supabase/supabase-js';

const getSupabase = (env) => createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY);

// GET /api/analytics/bot-stats?botId=...&range=7d|30d|90d
export const getBotStats = async ({ request, user, env, corsHeaders }) => {
  try {
    const url = new URL(request.url);
    const botId = url.searchParams.get('botId');
    const range = url.searchParams.get('range') || '7d';

    if (!botId) {
      return new Response(JSON.stringify({ error: 'botId is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    const supabase = getSupabase(env);

    // Verify access
    const { error: botError } = await supabase
      .from('bots')
      .select('id')
      .eq('id', botId)
      .eq('user_id', user.id)
      .single();

    if (botError) {
      return new Response(JSON.stringify({ error: 'Bot not found or access denied' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    // Date range
    const now = new Date();
    const start = new Date(now);
    if (range === '90d') start.setDate(now.getDate() - 90);
    else if (range === '30d') start.setDate(now.getDate() - 30);
    else start.setDate(now.getDate() - 7);

    // Fetch conversations for bot in range
    const { data: conversations, error: convError } = await supabase
      .from('conversations')
      .select('id, created_at')
      .eq('bot_id', botId)
      .gte('created_at', start.toISOString());

    if (convError) {
      return new Response(JSON.stringify({ error: convError.message }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    const conversationIds = (conversations || []).map((c) => c.id);

    // Messages in range
    let totalMessages = 0;
    let uniqueUsers = 0; // No auth user per message; approximate by conversations count
    let averageResponseTime = null; // Placeholder if not tracked
    let dailyUsageMap = new Map();

    if (conversationIds.length > 0) {
      const { data: messages, error: messagesError } = await supabase
        .from('messages')
        .select('created_at, role, conversation_id')
        .in('conversation_id', conversationIds)
        .gte('created_at', start.toISOString());

      if (!messagesError && messages) {
        totalMessages = messages.length;
        uniqueUsers = conversations.length; // proxy based on distinct conversations

        for (const m of messages) {
          const d = new Date(m.created_at);
          const key = `${d.getFullYear()}-${(d.getMonth()+1).toString().padStart(2,'0')}-${d.getDate().toString().padStart(2,'0')}`;
          dailyUsageMap.set(key, (dailyUsageMap.get(key) || 0) + 1);
        }
      }
    }

    // Top questions: naive approach using first 80 chars of user messages
    const { data: userMsgs } = await supabase
      .from('messages')
      .select('content, role, created_at, conversation_id')
      .in('conversation_id', conversationIds)
      .gte('created_at', start.toISOString());

    const freq = new Map();
    for (const m of userMsgs || []) {
      if (m.role !== 'user') continue;
      const q = (m.content || '').trim().slice(0, 80);
      if (!q) continue;
      freq.set(q, (freq.get(q) || 0) + 1);
    }
    const topQuestions = Array.from(freq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([question, count]) => ({ question, count }));

    // Build dailyUsage array covering range
    const dailyUsage = [];
    const day = new Date(start);
    while (day <= now) {
      const key = `${day.getFullYear()}-${(day.getMonth()+1).toString().padStart(2,'0')}-${day.getDate().toString().padStart(2,'0')}`;
      dailyUsage.push({ date: key, messages: dailyUsageMap.get(key) || 0 });
      day.setDate(day.getDate() + 1);
    }

    const payload = {
      totalMessages,
      uniqueUsers,
      averageResponseTime: averageResponseTime ?? 0,
      topQuestions,
      dailyUsage,
    };

    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Failed to compute analytics' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders },
    });
  }
};


